from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_organizer
from app.db.session import get_session
from app.schemas.event import EventCreate, EventPage, EventRead, EventUpdate
from app.services import events

router = APIRouter(prefix="/events", tags=["events"])
Session = Annotated[AsyncSession, Depends(get_session)]
Organizer = Depends(require_organizer)


@router.get("", response_model=EventPage)
async def list_events(
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await events.list_events(session, limit, offset)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: UUID, session: Session):
    return await events.get_event(session, event_id)


@router.post("", response_model=EventRead, status_code=201, dependencies=[Organizer])
async def create_event(data: EventCreate, session: Session):
    return await events.create_event(session, data)


@router.patch("/{event_id}", response_model=EventRead, dependencies=[Organizer])
async def update_event(event_id: UUID, data: EventUpdate, session: Session):
    return await events.update_event(session, event_id, data)


@router.delete("/{event_id}", status_code=204, dependencies=[Organizer])
async def delete_event(event_id: UUID, session: Session):
    await events.delete_event(session, event_id)
    return Response(status_code=204)
