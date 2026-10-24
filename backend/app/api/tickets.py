from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.events import Session
from app.api.registrations import Participant
from app.core.security import require_organizer
from app.schemas.ticket import CheckInResult, TicketCode, TicketRead, TicketVerification
from app.services import tickets

router = APIRouter(tags=["tickets"])


@router.get("/registrations/{registration_id}/ticket", response_model=TicketRead | None)
async def get_ticket(
    registration_id: UUID, session: Session, token: Participant, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return await tickets.get_owned_ticket(session, registration_id, token)


@router.post(
    "/events/{event_id}/tickets/verify",
    response_model=TicketVerification,
    dependencies=[Depends(require_organizer)],
)
async def verify(
    event_id: UUID, data: TicketCode, session: Session, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return await tickets.verify_ticket(session, event_id, data.code)


@router.post(
    "/events/{event_id}/check-in",
    response_model=CheckInResult,
    dependencies=[Depends(require_organizer)],
)
async def check_in(
    event_id: UUID, data: TicketCode, session: Session, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return await tickets.check_in(session, event_id, data.code)
