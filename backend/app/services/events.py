from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.registration import Registration
from app.schemas.event import EventCreate, EventUpdate
from app.services.errors import Conflict


class EventNotFound(Exception):
    pass


async def list_events(session: AsyncSession, limit: int, offset: int):
    total = await session.scalar(select(func.count()).select_from(Event))
    items = await session.scalars(
        select(Event).order_by(Event.starts_at, Event.id).limit(limit).offset(offset)
    )
    return {"items": items.all(), "total": total, "limit": limit, "offset": offset}


async def get_event(
    session: AsyncSession, event_id: UUID, *, lock: bool = False
) -> Event:
    query = select(Event).where(Event.id == event_id)
    if lock:
        query = query.with_for_update()
    event = await session.scalar(query)
    if event is None:
        raise EventNotFound
    return event


async def create_event(session: AsyncSession, data: EventCreate) -> Event:
    async with session.begin():
        event = Event(**data.model_dump())
        session.add(event)
        await session.flush()
    return event


async def update_event(
    session: AsyncSession, event_id: UUID, data: EventUpdate
) -> Event:
    async with session.begin():
        event = await get_event(session, event_id, lock=True)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("capacity", event.capacity) < event.confirmed_count:
            raise Conflict(
                "Вместимость не может быть меньше числа подтверждённых участников"
            )
        if "starts_at" in changes and changes["starts_at"] != event.starts_at:
            event.schedule_version += 1
        for field, value in changes.items():
            setattr(event, field, value)
        await session.flush()
        from app.services.registrations import promote_waiters

        await promote_waiters(session, event)
        await session.refresh(event)
    return event


async def delete_event(session: AsyncSession, event_id: UUID) -> None:
    async with session.begin():
        event = await get_event(session, event_id, lock=True)
        if await session.scalar(
            select(Registration.id).where(Registration.event_id == event_id).limit(1)
        ):
            raise Conflict("Нельзя удалить мероприятие с историей регистраций")
        await session.delete(event)
