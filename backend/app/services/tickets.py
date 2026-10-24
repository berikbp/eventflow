from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.registration import Registration
from app.models.ticket import Ticket
from app.schemas.ticket import CheckInResult, TicketRead, TicketVerification
from app.services.errors import Conflict, TicketNotFound
from app.services.events import get_event


async def active_ticket(session: AsyncSession, registration_id: UUID) -> Ticket | None:
    return await session.scalar(
        select(Ticket).where(
            Ticket.registration_id == registration_id, Ticket.revoked_at.is_(None)
        )
    )


async def issue_ticket(
    session: AsyncSession, registration: Registration, *, promoted: bool = False
) -> Ticket:
    # Caller holds the event lock and owns the surrounding transaction.
    existing = await active_ticket(session, registration.id)
    if existing is not None:
        return existing
    ticket = Ticket(registration_id=registration.id)
    session.add(ticket)
    await session.flush()
    from app.services.notifications import ticket_notifications

    await ticket_notifications(session, registration, ticket, promoted)
    return ticket


async def revoke_ticket(session: AsyncSession, registration_id: UUID) -> None:
    ticket = await active_ticket(session, registration_id)
    if ticket is None:
        return
    if ticket.checked_in_at is not None:
        raise Conflict("Нельзя отменить участие после check-in")
    ticket.revoked_at = datetime.now(UTC)
    await session.flush()


async def get_owned_ticket(
    session: AsyncSession, registration_id: UUID, token: str
) -> TicketRead | None:
    from app.services.registrations import owned_registration

    await owned_registration(session, registration_id, token)
    # The registration status and active ticket are read in the same snapshot.
    ticket = await session.scalar(
        select(Ticket)
        .join(Registration, Registration.id == Ticket.registration_id)
        .where(
            Registration.id == registration_id,
            Registration.status == "confirmed",
            Ticket.revoked_at.is_(None),
        )
        .execution_options(populate_existing=True)
    )
    return TicketRead.model_validate(ticket) if ticket else None


def verification(ticket: Ticket, registration: Registration) -> TicketVerification:
    state = (
        "revoked"
        if ticket.revoked_at is not None or registration.status != "confirmed"
        else ("checked_in" if ticket.checked_in_at is not None else "valid")
    )
    return TicketVerification(
        **TicketRead.model_validate(ticket).model_dump(),
        event_id=registration.event_id,
        email=registration.email,
        status=state,
        revoked_at=ticket.revoked_at,
    )


async def find_ticket(session: AsyncSession, event_id: UUID, code: str):
    row = (
        await session.execute(
            select(Ticket, Registration)
            .join(Registration, Registration.id == Ticket.registration_id)
            .where(Registration.event_id == event_id, Ticket.code == code)
        )
    ).first()
    if row is None:
        raise TicketNotFound
    return row


async def verify_ticket(
    session: AsyncSession, event_id: UUID, code: str
) -> TicketVerification:
    await get_event(session, event_id)
    ticket, registration = await find_ticket(session, event_id, code)
    return verification(ticket, registration)


async def check_in(session: AsyncSession, event_id: UUID, code: str) -> CheckInResult:
    async with session.begin():
        # Same lock order as cancellation/promotion/capacity changes.
        await get_event(session, event_id, lock=True)
        ticket, registration = await find_ticket(session, event_id, code)
        if ticket.revoked_at is not None or registration.status != "confirmed":
            raise Conflict("Билет отозван или регистрация не подтверждена")
        repeated = ticket.checked_in_at is not None
        if not repeated:
            ticket.checked_in_at = datetime.now(UTC)
            await session.flush()
        return CheckInResult(
            ticket=verification(ticket, registration), already_checked_in=repeated
        )
