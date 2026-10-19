from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
async def application():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://test:test@127.0.0.1:1/test",
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def client(application):
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://test"
    ) as http_client:
        yield http_client


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_executes_database_query(client, application):
    connection = AsyncMock()
    manager = AsyncMock()
    manager.__aenter__.return_value = connection
    engine = MagicMock()
    engine.connect.return_value = manager
    original = application.state.engine
    application.state.engine = engine
    try:
        response = await client.get("/health/ready")
    finally:
        application.state.engine = original
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert str(connection.execute.call_args.args[0]) == "SELECT 1"


async def test_database_unavailable_returns_503_without_connection_details(
    client, application
):
    manager = AsyncMock()
    manager.__aenter__.side_effect = OSError("private connection details")
    engine = MagicMock()
    engine.connect.return_value = manager
    original = application.state.engine
    application.state.engine = engine
    try:
        response = await client.get("/health/ready")
    finally:
        application.state.engine = original
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
