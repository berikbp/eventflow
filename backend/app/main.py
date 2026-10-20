from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.events import router as events_router
from app.api.health import router
from app.api.organizer import router as organizer_router
from app.core.config import Settings
from app.services.events import EventNotFound


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        config = settings or Settings()
        app.state.settings = config
        app.state.engine = create_async_engine(
            str(config.database_url), pool_pre_ping=True, connect_args={"timeout": 5}
        )
        app.state.sessions = async_sessionmaker(
            app.state.engine, expire_on_commit=False
        )
        try:
            yield
        finally:
            await app.state.engine.dispose()

    app = FastAPI(title="EventFlow API", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    app.include_router(events_router)
    app.include_router(organizer_router)

    @app.exception_handler(EventNotFound)
    async def event_not_found(request: Request, exc: EventNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404, content={"detail": "Мероприятие не найдено"}
        )

    return app


app = create_app()
