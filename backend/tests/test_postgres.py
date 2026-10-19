import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Set TEST_DATABASE_URL for real PostgreSQL",
)
async def test_readiness_with_real_postgres():
    settings = Settings(_env_file=None, database_url=os.environ["TEST_DATABASE_URL"])
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            assert response.json() == {"status": "ok", "database": "ok"}
