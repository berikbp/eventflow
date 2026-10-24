from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.events import router as events_router
from app.api.health import router
from app.api.organizer import router as organizer_router
from app.api.realtime import router as realtime_router
from app.api.registrations import router as registrations_router
from app.api.tickets import router as tickets_router
from app.core.config import Settings
from app.services.errors import Conflict, RegistrationNotFound, TicketNotFound
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
    app.include_router(registrations_router)
    app.include_router(tickets_router)
    app.include_router(realtime_router)

    @app.exception_handler(TicketNotFound)
    async def ticket_not_found(request: Request, exc: TicketNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404, content={"detail": "Билет не найден для этого мероприятия"}
        )

    @app.exception_handler(Conflict)
    async def conflict(request: Request, exc: Conflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(RegistrationNotFound)
    async def registration_not_found(
        request: Request, exc: RegistrationNotFound
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Регистрация не найдена или ссылка недействительна"},
        )

    @app.exception_handler(EventNotFound)
    async def event_not_found(request: Request, exc: EventNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404, content={"detail": "Мероприятие не найдено"}
        )

    return app


app = create_app()
