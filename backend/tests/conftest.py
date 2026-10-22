import os
from uuid import uuid4

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from app.core.config import Settings
from app.main import create_app

TOKEN = "test-organizer-token-for-eventflow-api"


@pytest.fixture
async def database():
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("Set TEST_DATABASE_URL for real PostgreSQL")
    url = os.environ["TEST_DATABASE_URL"]
    schema = "test_events_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": schema}},
    )
    try:
        async with engine.begin() as connection:

            def migrate(sync_connection):
                cfg = Config("alembic.ini")
                cfg.attributes["connection"] = sync_connection
                command.upgrade(cfg, "head")

            await connection.run_sync(migrate)
        yield engine
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            # Only the UUID-named schema created by this fixture is removed.
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin.dispose()


@pytest.fixture
async def client(database):
    settings = Settings(
        _env_file=None,
        database_url=os.environ["TEST_DATABASE_URL"],
        organizer_token=TOKEN,
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        original = app.state.engine
        app.state.engine = database
        app.state.sessions = async_sessionmaker(database, expire_on_commit=False)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as http:
                yield http
        finally:
            app.state.engine = original
