"""Database-backed outbox worker. SMTP is outside database transactions/locks."""

import asyncio
import logging
import smtplib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.models.event import Event
from app.models.notification import Notification
from app.models.registration import Registration
from app.models.ticket import Ticket
from app.services.notifications import schedule_reminders

logger = logging.getLogger(__name__)
SUBJECTS = {
    "confirmation": "Регистрация подтверждена",
    "promotion": "Вы получили место из листа ожидания",
    "reminder": "Напоминание о мероприятии",
    "rescheduled": "Время мероприятия изменилось",
}


@dataclass
class Delivery:
    id: UUID
    lease_token: UUID
    message: EmailMessage


def eligible(now: datetime):
    return or_(
        and_(Notification.status == "pending", Notification.available_at <= now),
        and_(Notification.status == "processing", Notification.lease_until <= now),
    )


async def claim(sessions: async_sessionmaker, settings: Settings) -> Delivery | None:
    now = datetime.now(UTC)
    async with sessions() as session:
        async with session.begin():
            # Lock an available parent directly: a busy event must not block
            # delivery for unrelated events. Keep Event -> Notification order.
            next_due = (
                select(func.min(Notification.available_at))
                .where(Notification.event_id == Event.id, eligible(now))
                .correlate(Event)
                .scalar_subquery()
            )
            event = await session.scalar(
                select(Event)
                .where(next_due.is_not(None))
                .order_by(next_due, Event.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if event is None:
                return None
            job = await session.scalar(
                select(Notification)
                .where(Notification.event_id == event.id, eligible(now))
                .order_by(Notification.available_at, Notification.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                return None
            registration = await session.get(Registration, job.registration_id)
            ticket = await session.scalar(
                select(Ticket).where(
                    Ticket.registration_id == registration.id,
                    Ticket.revoked_at.is_(None),
                )
            )
            valid = registration.status in {"confirmed", "waiting"}
            if job.kind != "rescheduled":
                valid = (
                    valid and registration.status == "confirmed" and ticket is not None
                )
            if job.kind in {"reminder", "rescheduled"}:
                valid = valid and job.schedule_version == event.schedule_version
            if job.kind == "reminder":
                valid = valid and event.starts_at > now
            if job.ticket_id is not None:
                valid = valid and ticket is not None and ticket.id == job.ticket_id
            if not valid:
                job.status = "skipped"
                job.lease_token = None
                job.lease_until = None
                return None
            job.status = "processing"
            job.attempts += 1
            job.lease_token = uuid4()
            job.lease_until = now + timedelta(
                seconds=settings.notification_lease_seconds
            )
            message = EmailMessage()
            message["From"] = settings.smtp_from
            message["To"] = registration.email
            message["Subject"] = f"EventFlow: {SUBJECTS[job.kind]}"
            message["Message-ID"] = f"<{job.id}@eventflow.local>"
            lines = [
                SUBJECTS[job.kind],
                event.title,
                f"Начало (UTC): {event.starts_at.isoformat()}",
                f"Статус: {registration.status}",
                f"Мероприятие: {settings.public_base_url.rstrip('/')}"
                f"/events/{event.id}",
            ]
            if ticket is not None and registration.status == "confirmed":
                lines.append(f"Код билета: {ticket.code}")
            lines.append("Личная ссылка управления остаётся у вас в браузере.")
            message.set_content("\n".join(lines))
            return Delivery(job.id, job.lease_token, message)


async def smtp_send(message: EmailMessage, settings: Settings) -> None:
    def send():
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
            smtp.send_message(message)

    await asyncio.to_thread(send)


async def deliver_one(
    sessions: async_sessionmaker,
    settings: Settings,
    sender: Callable[[EmailMessage, Settings], Awaitable[None]] = smtp_send,
) -> bool:
    delivery = await claim(sessions, settings)
    if delivery is None:
        return False
    error = None
    try:
        await sender(delivery.message, settings)
    except Exception as exc:
        # Never log recipient, ticket, SMTP response or credentials.
        error = type(exc).__name__[:100]
        logger.warning("SMTP attempt failed (%s)", error)
    async with sessions() as session:
        async with session.begin():
            job = await session.scalar(
                select(Notification)
                .where(
                    Notification.id == delivery.id,
                    Notification.status == "processing",
                    Notification.lease_token == delivery.lease_token,
                )
                .with_for_update()
            )
            if job is not None:
                job.status = "pending" if error else "sent"
                job.last_error = error
                job.sent_at = None if error else datetime.now(UTC)
                job.available_at = datetime.now(UTC) + timedelta(
                    seconds=min(300, 2 ** min(job.attempts, 8))
                )
                job.lease_until = None
                job.lease_token = None
    return True


async def run(settings: Settings) -> None:
    engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        while True:
            try:
                async with sessions.begin() as session:
                    await schedule_reminders(session)
                for _ in range(25):
                    if not await deliver_one(sessions, settings):
                        break
            except Exception as exc:
                logger.error(
                    "Outbox iteration failed (%s); retrying", type(exc).__name__
                )
            await asyncio.sleep(settings.worker_interval)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run(Settings()))
