"""Outbox writes only: called inside the business transaction, never sends SMTP."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import String, cast, func, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.notification import Notification
from app.models.registration import Registration
from app.models.ticket import Ticket


async def enqueue(
    session: AsyncSession,
    event: Event,
    registration: Registration,
    kind: str,
    *,
    ticket: Ticket | None = None,
) -> None:
    now = datetime.now(UTC)
    due = max(now, event.starts_at - timedelta(hours=24)) if kind == "reminder" else now
    identity = ticket.id if kind in {"confirmation", "promotion"} else registration.id
    key = f"{kind}:{identity}"
    if kind in {"reminder", "rescheduled"}:
        key += f":{event.schedule_version}"
    statement = insert(Notification).values(
        event_id=event.id,
        registration_id=registration.id,
        ticket_id=ticket.id if ticket else None,
        kind=kind,
        deduplication_key=key,
        schedule_version=event.schedule_version,
        due_at=due,
        available_at=due,
    )
    if kind == "reminder":
        # A cancelled participant may rejoin before this schedule starts.
        statement = statement.on_conflict_do_update(
            index_elements=[Notification.deduplication_key],
            set_={"status": "pending", "due_at": due, "available_at": due},
            where=Notification.status == "skipped",
        )
    else:
        statement = statement.on_conflict_do_nothing(
            index_elements=[Notification.deduplication_key]
        )
    await session.execute(statement)


async def ticket_notifications(
    session: AsyncSession, registration: Registration, ticket: Ticket, promoted: bool
) -> None:
    event = await session.get(Event, registration.event_id)
    await enqueue(
        session,
        event,
        registration,
        "promotion" if promoted else "confirmation",
        ticket=ticket,
    )
    await enqueue(session, event, registration, "reminder")


async def reschedule_notifications(session: AsyncSession, event: Event) -> None:
    registrations = await session.scalars(
        select(Registration).where(
            Registration.event_id == event.id,
            Registration.status.in_(["confirmed", "waiting"]),
        )
    )
    for registration in registrations:
        await enqueue(session, event, registration, "rescheduled")
        if registration.status == "confirmed":
            await enqueue(session, event, registration, "reminder")


async def schedule_reminders(session: AsyncSession) -> None:
    """Repair/backfill missing reminders, also for confirmations predating Phase 5."""
    now = datetime.now(UTC)
    due = func.greatest(now, Event.starts_at - timedelta(hours=24))
    # INSERT SELECT is idempotent and does not need to lock business rows.
    statement = (
        insert(Notification)
        .from_select(
            [
                "id",
                "event_id",
                "registration_id",
                "kind",
                "deduplication_key",
                "schedule_version",
                "due_at",
                "available_at",
            ],
            select(
                func.gen_random_uuid(),
                Event.id,
                Registration.id,
                literal("reminder"),
                literal("reminder:")
                + cast(Registration.id, String)
                + literal(":")
                + cast(Event.schedule_version, String),
                Event.schedule_version,
                due,
                due,
            )
            .join(Registration, Registration.event_id == Event.id)
            .where(Registration.status == "confirmed", Event.starts_at > now),
        )
        .on_conflict_do_nothing(index_elements=[Notification.deduplication_key])
    )
    await session.execute(statement)
