import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from alembic import command
from app.seed import seed_events

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Set TEST_DATABASE_URL for real PostgreSQL",
)
TOKEN = "test-organizer-token-for-eventflow-api"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


def payload():
    return {
        "title": "  PostgreSQL meetup  ",
        "description": "Transactions",
        "starts_at": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
        "capacity": 30,
    }


async def test_full_crud_and_partial_update(client):
    assert (await client.get("/events")).json()["items"] == []
    response = await client.post("/events", json=payload(), headers=AUTH)
    assert response.status_code == 201
    event = response.json()
    assert event["title"] == "PostgreSQL meetup"
    assert event["schedule_version"] == 1
    assert "token" not in str(event)
    path = f"/events/{event['id']}"
    assert (await client.get(path)).json() == event
    page = (await client.get("/events?limit=1&offset=0")).json()
    assert page["total"] == 1 and page["items"][0]["id"] == event["id"]
    changed = await client.patch(path, json={"title": "Changed"}, headers=AUTH)
    assert changed.status_code == 200
    assert changed.json()["capacity"] == 30
    assert changed.json()["schedule_version"] == 1
    starts_at = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    changed = await client.patch(path, json={"starts_at": starts_at}, headers=AUTH)
    assert changed.json()["schedule_version"] == 2
    repeated = await client.patch(path, json={"starts_at": starts_at}, headers=AUTH)
    assert repeated.json()["schedule_version"] == 2
    assert (await client.delete(path, headers=AUTH)).status_code == 204
    assert (await client.get(path)).status_code == 404
    assert (await client.get("/events")).json()["total"] == 0


async def test_mutations_require_organizer(client):
    for auth in ({}, {"Authorization": "Bearer wrong"}):
        assert (
            await client.post("/events", json=payload(), headers=auth)
        ).status_code == 401
        path = f"/events/{uuid4()}"
        assert (
            await client.patch(path, json={"title": "x"}, headers=auth)
        ).status_code == 401
        assert (await client.delete(path, headers=auth)).status_code == 401
    assert (await client.get("/organizer/session", headers=AUTH)).status_code == 200
    assert (await client.get("/organizer/session")).status_code == 401


async def test_invalid_requests_and_missing_events(client):
    assert (
        await client.post("/events", json=payload() | {"capacity": 0}, headers=AUTH)
    ).status_code == 422
    assert (
        await client.post(
            "/events",
            json=payload() | {"starts_at": "2099-01-01T12:00:00"},
            headers=AUTH,
        )
    ).status_code == 422
    for query in ("limit=0", "limit=101", "offset=-1"):
        assert (await client.get(f"/events?{query}")).status_code == 422
    assert (await client.get("/events/not-a-uuid")).status_code == 422
    path = f"/events/{uuid4()}"
    assert (await client.get(path)).status_code == 404
    assert (
        await client.patch(path, json={"title": "New"}, headers=AUTH)
    ).status_code == 404
    assert (await client.delete(path, headers=AUTH)).status_code == 404


async def test_pagination_stable_order(client):
    for title in ("A", "B", "C"):
        assert (
            await client.post(
                "/events", json=payload() | {"title": title}, headers=AUTH
            )
        ).status_code == 201
    first = (await client.get("/events?limit=2")).json()
    second = (await client.get("/events?limit=2&offset=2")).json()
    assert first["total"] == second["total"] == 3
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert len({e["id"] for e in first["items"] + second["items"]}) == 3


async def test_database_constraint_and_migration_roundtrip(database):
    with pytest.raises(IntegrityError):
        async with database.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO events (id,title,description,starts_at,capacity) "
                    "VALUES (:id,'Test','',now(),0)"
                ),
                {"id": uuid4()},
            )
    async with database.begin() as connection:

        def roundtrip(sync_connection):
            cfg = Config("alembic.ini")
            cfg.attributes["connection"] = sync_connection
            command.check(cfg)
            command.downgrade(cfg, "base")
            command.upgrade(cfg, "head")
            command.check(cfg)

        await connection.run_sync(roundtrip)
        assert await connection.scalar(text("SELECT count(*) FROM events")) == 0


async def test_demo_seed_is_idempotent(database):
    async with async_sessionmaker(database)() as session:
        await seed_events(session)
        await seed_events(session)
        assert await session.scalar(text("SELECT count(*) FROM events")) == 2


async def test_search_filters_results_and_total_with_literal_wildcards(client):
    for title, description in [
        ("Community Python", "Meet friends"),
        ("PostgreSQL workshop", "Learn PYTHON SQL"),
        ("100% useful", "literal_percent"),
    ]:
        response = await client.post(
            "/events",
            json=payload()
            | {
                "title": title,
                "description": description,
            },
            headers=AUTH,
        )
        assert response.status_code == 201
    found = (await client.get("/events", params={"q": "python", "limit": 1})).json()
    assert found["total"] == 2 and len(found["items"]) == 1
    second = (
        await client.get("/events", params={"q": "PYTHON", "limit": 1, "offset": 1})
    ).json()
    assert second["total"] == 2
    assert found["items"][0]["id"] != second["items"][0]["id"]
    literal = (await client.get("/events", params={"q": "%"})).json()
    assert literal["total"] == 1 and literal["items"][0]["title"] == "100% useful"
    assert (await client.get("/events", params={"q": "unmatched"})).json()["total"] == 0


async def test_date_filters_are_timezone_aware_and_half_open(client):
    base = datetime.now(UTC) + timedelta(days=2)
    for days in [0, 2, 4]:
        assert (
            await client.post(
                "/events",
                headers=AUTH,
                json=payload()
                | {
                    "title": str(days),
                    "starts_at": (base + timedelta(days=days)).isoformat(),
                },
            )
        ).status_code == 201
    page = (
        await client.get(
            "/events",
            params={
                "starts_after": base.isoformat(),
                "starts_before": (base + timedelta(days=4)).isoformat(),
            },
        )
    ).json()
    assert page["total"] == 2 and [item["title"] for item in page["items"]] == [
        "0",
        "2",
    ]
    assert (
        await client.get("/events", params={"starts_after": "2099-01-01T12:00:00"})
    ).status_code == 422
    assert (await client.get("/events", params={"q": "x" * 201})).status_code == 422
    assert (
        await client.get(
            "/events",
            params={
                "starts_after": (base + timedelta(days=5)).isoformat(),
                "starts_before": base.isoformat(),
            },
        )
    ).status_code == 422
