from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.health import router
from app.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        config = settings or Settings()
        app.state.engine = create_async_engine(
            str(config.database_url), pool_pre_ping=True, connect_args={"timeout": 5}
        )
        try:
            yield
        finally:
            await app.state.engine.dispose()

    app = FastAPI(title="EventFlow API", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
