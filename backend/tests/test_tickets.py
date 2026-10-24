import asyncio
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command

AUTH = {"Authorization": "Bearer test-organizer-token-for-eventflow-api"}


async def event(client, capacity=1):
    response = await client.post(
        "/events",
        headers=AUTH,
        json={
            "title": "Ticket test",
            "capacity": capacity,
            "starts_at": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def register(client, eid, email, token=None):
    token = token or token_urlsafe(32)
    response = await client.post(
        f"/events/{eid}/registrations",
        json={"email": email},
        headers={"X-Registration-Token": token},
    )
    assert response.status_code == 200
    return response.json(), token


async def ticket(client, record, token):
    response = await client.get(
        f"/registrations/{record['id']}/ticket",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    return response.json()


async def cancel(client, record, token, action="cancel"):
    return await client.post(
        f"/registrations/{record['id']}/{action}",
        headers={"Authorization": f"Bearer {token}"},
    )


async def check_in(client, eid, code):
    return await client.post(
        f"/events/{eid}/check-in", json={"code": code}, headers=AUTH
    )


async def verify(client, eid, code):
    return await client.post(
        f"/events/{eid}/tickets/verify", json={"code": code}, headers=AUTH
    )


async def test_ticket_issuance_retry_access_and_code_normalization(client):
    eid = await event(client)
    record, token = await register(client, eid, "person@example.com")
    issued = await ticket(client, record, token)
    assert len(issued["code"]) == 32 and issued["checked_in_at"] is None
    retried, _ = await register(client, eid, "person@example.com", token)
    assert (await ticket(client, retried, token)) == issued
    waiting, secret = await register(client, eid, "waiting@example.com")
    assert await ticket(client, waiting, secret) is None
    assert (
        await client.get(f"/registrations/{record['id']}/ticket")
    ).status_code == 401
    assert (
        await client.get(
            f"/registrations/{record['id']}/ticket",
            headers={"Authorization": "Bearer wrong"},
        )
    ).status_code == 404
    formatted = "-".join(issued["code"].lower()[i : i + 4] for i in range(0, 32, 4))
    response = await verify(client, eid, formatted)
    assert response.status_code == 200 and response.json()["status"] == "valid"
    assert response.json()["email"] == "person@example.com"
    assert (await client.get(f"/events/{eid}/availability")).json()["checked_in"] == 0


async def test_revocation_promotion_and_rejoin_issue_new_ticket(client, database):
    eid = await event(client)
    first, token = await register(client, eid, "first@example.com")
    waiting, token2 = await register(client, eid, "second@example.com")
    old = await ticket(client, first, token)
    assert (await cancel(client, first, token)).status_code == 200
    assert await ticket(client, first, token) is None
    promoted = await ticket(client, waiting, token2)
    assert promoted and promoted["code"] != old["code"]
    assert (await verify(client, eid, old["code"])).json()["status"] == "revoked"
    assert (await check_in(client, eid, old["code"])).status_code == 409
    assert (await cancel(client, first, token, "rejoin")).status_code == 200
    assert await ticket(client, first, token) is None
    assert (await cancel(client, waiting, token2)).status_code == 200
    new = await ticket(client, first, token)
    assert new["code"] not in {old["code"], promoted["code"]}
    assert (await check_in(client, eid, old["code"])).status_code == 409
    async with database.connect() as connection:
        assert (
            await connection.scalar(text("SELECT count(DISTINCT code) FROM tickets"))
            == 3
        )
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM tickets WHERE revoked_at IS NULL")
            )
            == 1
        )


async def test_checkin_repeat_counter_and_cancellation_guard(client):
    eid = await event(client)
    record, token = await register(client, eid, "person@example.com")
    waiting, secret = await register(client, eid, "waiting@example.com")
    issued = await ticket(client, record, token)
    first = await check_in(client, eid, issued["code"])
    second = await check_in(client, eid, issued["code"])
    assert first.status_code == second.status_code == 200
    assert (
        not first.json()["already_checked_in"] and second.json()["already_checked_in"]
    )
    assert (
        first.json()["ticket"]["checked_in_at"]
        == second.json()["ticket"]["checked_in_at"]
    )
    counts = (await client.get(f"/events/{eid}/availability")).json()
    assert counts["checked_in"] == counts["confirmed"] == 1
    assert (await cancel(client, record, token)).status_code == 409
    assert await ticket(client, waiting, secret) is None
    listing = (await client.get(f"/events/{eid}/registrations", headers=AUTH)).json()
    assert (
        listing["items"][0]["checked_in_at"] == first.json()["ticket"]["checked_in_at"]
    )
    assert (await verify(client, eid, issued["code"])).json()["status"] == "checked_in"


async def test_concurrent_checkin_records_one_admission(client, database):
    eid = await event(client)
    record, token = await register(client, eid, "person@example.com")
    issued = await ticket(client, record, token)
    barrier = asyncio.Barrier(20)

    async def submit():
        await barrier.wait()
        return await check_in(client, eid, issued["code"])

    results = await asyncio.wait_for(asyncio.gather(*(submit() for _ in range(20))), 30)
    assert all(result.status_code == 200 for result in results)
    assert sum(not result.json()["already_checked_in"] for result in results) == 1
    assert len({result.json()["ticket"]["checked_in_at"] for result in results}) == 1
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM tickets WHERE checked_in_at IS NOT NULL")
            )
            == 1
        )
        assert await connection.scalar(text("SELECT confirmed_count FROM events")) == 1


async def test_checkin_racing_cancellation_never_admits_revoked_ticket(client):
    eid = await event(client)
    record, token = await register(client, eid, "person@example.com")
    waiting, secret = await register(client, eid, "waiting@example.com")
    issued = await ticket(client, record, token)
    barrier = asyncio.Barrier(2)

    async def enter():
        await barrier.wait()
        return await check_in(client, eid, issued["code"])

    async def leave():
        await barrier.wait()
        return await cancel(client, record, token)

    entered, cancelled = await asyncio.wait_for(asyncio.gather(enter(), leave()), 30)
    assert sorted([entered.status_code, cancelled.status_code]) == [200, 409]
    result = (await verify(client, eid, issued["code"])).json()
    if entered.status_code == 200:
        assert result["status"] == "checked_in"
        assert await ticket(client, waiting, secret) is None
    else:
        assert result["status"] == "revoked"
        assert await ticket(client, waiting, secret) is not None


async def test_capacity_promotion_issues_ticket_atomically(client):
    eid = await event(client)
    await register(client, eid, "first@example.com")
    record, token = await register(client, eid, "waiting@example.com")
    assert await ticket(client, record, token) is None
    response = await client.patch(f"/events/{eid}", json={"capacity": 2}, headers=AUTH)
    assert response.status_code == 200
    assert await ticket(client, record, token) is not None


async def test_checkin_access_invalid_code_and_wrong_event(client):
    eid = await event(client)
    record, token = await register(client, eid, "person@example.com")
    issued = await ticket(client, record, token)
    other = await event(client)
    assert (await verify(client, other, issued["code"])).status_code == 404
    assert (await check_in(client, other, issued["code"])).status_code == 404
    assert (await check_in(client, eid, "0" * 32)).status_code == 404
    assert (await check_in(client, eid, "invalid")).status_code == 422
    for suffix in ("check-in", "tickets/verify"):
        response = await client.post(
            f"/events/{eid}/{suffix}", json={"code": issued["code"]}
        )
        assert response.status_code == 401
    assert (await client.get(f"/events/{eid}/availability")).json()["checked_in"] == 0


async def test_ticket_unique_code_and_active_registration_constraints(client, database):
    eid = await event(client, 2)
    first, token = await register(client, eid, "first@example.com")
    second, _ = await register(client, eid, "second@example.com")
    code = (await ticket(client, first, token))["code"]
    with pytest.raises(IntegrityError):
        async with database.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO tickets (id,registration_id,code,revoked_at) "
                    "VALUES (:id,:rid,:code,now())"
                ),
                {"id": uuid4(), "rid": second["id"], "code": code},
            )
    with pytest.raises(IntegrityError):
        async with database.begin() as connection:
            await connection.execute(
                text("INSERT INTO tickets (id,registration_id) VALUES (:id,:rid)"),
                {"id": uuid4(), "rid": first["id"]},
            )


async def test_ticket_issuance_rolls_back_with_registration(client, database):
    eid = await event(client)
    async with database.connect() as connection:
        transaction = await connection.begin()
        rid = uuid4()
        await connection.execute(
            text(
                "INSERT INTO registrations "
                "(id,event_id,email,token_hash,status,queue_order) "
                "VALUES (:id,:eid,'rollback@example.com',:hash,'confirmed',1)"
            ),
            {"id": rid, "eid": eid, "hash": "f" * 64},
        )
        await connection.execute(
            text("INSERT INTO tickets (id,registration_id) VALUES (:id,:rid)"),
            {"id": uuid4(), "rid": rid},
        )
        await transaction.rollback()
        assert await connection.scalar(text("SELECT count(*) FROM tickets")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM registrations")) == 0
        assert await connection.scalar(text("SELECT confirmed_count FROM events")) == 0


async def test_migration_backfills_existing_confirmed_only(client, database):
    eid = await event(client)
    first, _ = await register(client, eid, "first@example.com")
    await register(client, eid, "waiting@example.com")
    async with database.begin() as connection:

        def migrate(sync_connection):
            cfg = Config("alembic.ini")
            cfg.attributes["connection"] = sync_connection
            command.downgrade(cfg, "0002_registrations")
            command.upgrade(cfg, "head")
            command.check(cfg)

        await connection.run_sync(migrate)
        assert await connection.scalar(text("SELECT count(*) FROM tickets")) == 1
        assert (
            str(await connection.scalar(text("SELECT registration_id FROM tickets")))
            == first["id"]
        )
