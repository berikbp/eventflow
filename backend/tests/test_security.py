import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.setup_local import initialize


async def test_empty_organizer_token_disables_writes():
    config = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://test:test@localhost/test",
        organizer_token="",
    )
    app = create_app(config)
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (await client.get("/organizer/session")).status_code == 503
            assert (await client.post("/events", json={})).status_code == 503


def test_short_token_rejected():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://a:b@localhost/db",
            organizer_token="short",
        )


def test_setup_is_idempotent_and_preserves_existing_env(tmp_path):
    (tmp_path / ".env.example").write_text("DATABASE_URL=example\nORGANIZER_TOKEN=\n")
    assert initialize(tmp_path)
    first = (tmp_path / ".env").read_text()
    assert "DATABASE_URL=example" in first
    assert len(first.split("ORGANIZER_TOKEN=")[1].strip()) >= 32
    assert not initialize(tmp_path)
    assert (tmp_path / ".env").read_text() == first
