"""SSE invalidation signals backed by committed PostgreSQL revisions."""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from hashlib import sha256

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.event import Event

router = APIRouter(tags=["realtime"])


async def revision_snapshot(sessions: async_sessionmaker) -> str:
    async with sessions() as session:
        rows = await session.execute(
            select(
                Event.id, Event.revision, Event.starts_at > datetime.now(UTC)
            ).order_by(Event.id)
        )
        return sha256(repr(rows.all()).encode()).hexdigest()


async def updates(
    sessions: async_sessionmaker, *, interval: float = 1
) -> AsyncIterator[str]:
    previous = None
    quiet = 0
    yield "retry: 2000\n\n"
    while True:
        try:
            current = await revision_snapshot(sessions)
        except (SQLAlchemyError, OSError, TimeoutError):
            # Closing prompts EventSource to reconnect and request a new snapshot.
            yield "event: unavailable\ndata: {}\n\n"
            return
        if current != previous:
            yield f"id: {current}\nevent: invalidate\ndata: {{}}\n\n"
            previous = current
            quiet = 0
        else:
            quiet += 1
            if quiet >= 10:
                yield "event: heartbeat\ndata: {}\n\n"
                quiet = 0
        # No connection/transaction is held between checks, including slow readers.
        await asyncio.sleep(interval)


@router.get("/updates")
async def stream(request: Request):
    # Initial invalidate is always emitted, also with Last-Event-ID on reconnect.
    # StreamingResponse cancels the generator on disconnect.
    return StreamingResponse(
        updates(request.app.state.sessions),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
