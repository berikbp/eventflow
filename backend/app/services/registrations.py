from datetime import UTC, datetime
from hashlib import sha256
from secrets import compare_digest
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.event import Event
from app.models.registration import Registration
from app.models.ticket import Ticket
from app.schemas.registration import Availability, RegistrationRead
from app.services.errors import Conflict, RegistrationNotFound
from app.services.events import EventNotFound, get_event
from app.services.tickets import issue_ticket, revoke_ticket


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def ensure_open(event: Event) -> None:
    if event.starts_at <= datetime.now(UTC):
        raise Conflict(
            "Регистрация и изменение участия закрыты: мероприятие уже началось"
        )


async def promote_waiters(session: AsyncSession, event: Event) -> None:
    # Caller must hold the event row lock. Triggers maintain confirmed_count.
    await session.refresh(event)
    if event.starts_at <= datetime.now(UTC):
        return
    free = event.capacity - event.confirmed_count
    if free <= 0:
        return
    waiting = await session.scalars(
        select(Registration)
        .where(Registration.event_id == event.id, Registration.status == "waiting")
        .order_by(Registration.queue_order)
        .limit(free)
    )
    promoted = waiting.all()
    for registration in promoted:
        registration.status = "confirmed"
    await session.flush()
    for registration in promoted:
        await issue_ticket(session, registration, promoted=True)
    await session.refresh(event)


def snapshot_query():
    waiting = aliased(Registration)
    position = (
        select(func.count())
        .select_from(waiting)
        .where(
            waiting.event_id == Registration.event_id,
            waiting.status == "waiting",
            waiting.queue_order <= Registration.queue_order,
        )
        .correlate(Registration)
        .scalar_subquery()
    )
    checked_in = (
        select(Ticket.checked_in_at)
        .where(Ticket.registration_id == Registration.id, Ticket.revoked_at.is_(None))
        .correlate(Registration)
        .scalar_subquery()
    )
    return select(Registration, position, checked_in).execution_options(
        populate_existing=True
    )


def serialize_registration(
    registration: Registration, position: int, checked_in_at: datetime | None
) -> RegistrationRead:
    return RegistrationRead(
        id=registration.id,
        event_id=registration.event_id,
        email=registration.email,
        status=registration.status,
        queue_order=registration.queue_order,
        queue_position=position if registration.status == "waiting" else None,
        created_at=registration.created_at,
        updated_at=registration.updated_at,
        checked_in_at=checked_in_at,
    )


async def read_registration(
    session: AsyncSession, registration: Registration
) -> RegistrationRead:
    row = (
        await session.execute(
            snapshot_query().where(Registration.id == registration.id)
        )
    ).one()
    return serialize_registration(*row)


async def register(
    session: AsyncSession, event_id: UUID, email: str, token: str
) -> RegistrationRead:
    async with session.begin():
        event = await get_event(session, event_id, lock=True)
        digest = hash_token(token)
        existing = await session.scalar(
            select(Registration).where(
                Registration.event_id == event_id, Registration.email == email
            )
        )
        if existing:
            if not compare_digest(existing.token_hash, digest):
                raise Conflict(
                    "Этот email уже зарегистрирован. "
                    "Используйте сохранённую ссылку управления."
                )
            return await read_registration(session, existing)
        ensure_open(event)
        reused = await session.scalar(
            select(Registration.id).where(
                Registration.event_id == event_id, Registration.token_hash == digest
            )
        )
        if reused:
            raise Conflict("Для новой регистрации требуется новый ключ управления")
        await promote_waiters(session, event)
        event.next_registration_order += 1
        registration = Registration(
            event_id=event_id,
            email=email,
            token_hash=digest,
            status="confirmed" if event.confirmed_count < event.capacity else "waiting",
            queue_order=event.next_registration_order,
        )
        session.add(registration)
        await session.flush()
        if registration.status == "confirmed":
            await issue_ticket(session, registration)
        return await read_registration(session, registration)


async def owned_registration(session: AsyncSession, registration_id: UUID, token: str):
    registration = await session.get(Registration, registration_id)
    if registration is None or not compare_digest(
        registration.token_hash, hash_token(token)
    ):
        raise RegistrationNotFound
    return registration


async def get_owned(session: AsyncSession, registration_id: UUID, token: str):
    registration = await owned_registration(session, registration_id, token)
    return await read_registration(session, registration)


async def change_participation(
    session: AsyncSession, registration_id: UUID, token: str, *, rejoin: bool = False
) -> RegistrationRead:
    async with session.begin():
        # Read parent identity first; never lock a registration before its event.
        registration = await owned_registration(session, registration_id, token)
        event = await get_event(session, registration.event_id, lock=True)
        await session.refresh(registration)
        target = "cancelled" if not rejoin else "active"
        if (target == "cancelled" and registration.status == "cancelled") or (
            rejoin and registration.status != "cancelled"
        ):
            return await read_registration(session, registration)
        ensure_open(event)
        if rejoin:
            await promote_waiters(session, event)
            event.next_registration_order += 1
            registration.queue_order = event.next_registration_order
            registration.status = (
                "confirmed" if event.confirmed_count < event.capacity else "waiting"
            )
        else:
            await revoke_ticket(session, registration.id)
            registration.status = "cancelled"
        await session.flush()
        if rejoin and registration.status == "confirmed":
            await issue_ticket(session, registration)
        await promote_waiters(session, event)
        await session.refresh(registration)
        return await read_registration(session, registration)


async def availability(session: AsyncSession, event_id: UUID) -> Availability:
    # One statement gives a consistent snapshot of capacity and status counters.
    waiting = (
        select(func.count())
        .select_from(Registration)
        .where(Registration.event_id == Event.id, Registration.status == "waiting")
        .correlate(Event)
        .scalar_subquery()
    )
    checked_in = (
        select(func.count())
        .select_from(Ticket)
        .join(Registration, Registration.id == Ticket.registration_id)
        .where(
            Registration.event_id == Event.id,
            Registration.status == "confirmed",
            Ticket.revoked_at.is_(None),
            Ticket.checked_in_at.is_not(None),
        )
        .correlate(Event)
        .scalar_subquery()
    )
    row = (
        await session.execute(
            select(Event, waiting, checked_in).where(Event.id == event_id)
        )
    ).first()
    if row is None:
        raise EventNotFound
    event, waiting_count, checked_in_count = row
    return Availability(
        capacity=event.capacity,
        confirmed=event.confirmed_count,
        waiting=waiting_count,
        available=event.capacity - event.confirmed_count,
        registration_open=event.starts_at > datetime.now(UTC),
        checked_in=checked_in_count,
    )


async def list_registrations(
    session: AsyncSession, event_id: UUID, limit: int, offset: int
):
    await get_event(session, event_id)
    total = await session.scalar(
        select(func.count())
        .select_from(Registration)
        .where(Registration.event_id == event_id)
    )
    rows = await session.execute(
        snapshot_query()
        .where(Registration.event_id == event_id)
        .order_by(Registration.queue_order)
        .limit(limit)
        .offset(offset)
    )
    return {
        "items": [serialize_registration(*row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
