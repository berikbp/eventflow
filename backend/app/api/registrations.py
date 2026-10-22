from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials

from app.api.events import Session
from app.core.security import bearer, require_organizer
from app.schemas.registration import (
    Availability,
    RegistrationCreate,
    RegistrationPage,
    RegistrationRead,
)
from app.services import registrations

router = APIRouter(tags=["registrations"])


async def participant_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if credentials is None:
        raise HTTPException(
            401, "Требуется ссылка управления", headers={"WWW-Authenticate": "Bearer"}
        )
    return credentials.credentials


Participant = Annotated[str, Depends(participant_token)]
RegistrationToken = Annotated[
    str,
    Header(
        alias="X-Registration-Token",
        min_length=43,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    ),
]


@router.post("/events/{event_id}/registrations", response_model=RegistrationRead)
async def register(
    event_id: UUID,
    data: RegistrationCreate,
    session: Session,
    response: Response,
    token: RegistrationToken,
):
    response.headers["Cache-Control"] = "no-store"
    return await registrations.register(session, event_id, str(data.email), token)


@router.get("/events/{event_id}/availability", response_model=Availability)
async def availability(event_id: UUID, session: Session):
    return await registrations.availability(session, event_id)


@router.get(
    "/events/{event_id}/registrations",
    response_model=RegistrationPage,
    dependencies=[Depends(require_organizer)],
)
async def list_registrations(
    event_id: UUID,
    session: Session,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await registrations.list_registrations(session, event_id, limit, offset)


@router.get("/registrations/{registration_id}", response_model=RegistrationRead)
async def get_registration(
    registration_id: UUID,
    session: Session,
    token: Participant,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await registrations.get_owned(session, registration_id, token)


@router.post("/registrations/{registration_id}/cancel", response_model=RegistrationRead)
async def cancel(
    registration_id: UUID,
    session: Session,
    token: Participant,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await registrations.change_participation(session, registration_id, token)


@router.post("/registrations/{registration_id}/rejoin", response_model=RegistrationRead)
async def rejoin(
    registration_id: UUID,
    session: Session,
    token: Participant,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await registrations.change_participation(
        session, registration_id, token, rejoin=True
    )
