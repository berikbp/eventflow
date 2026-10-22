import asyncio
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

AUTH = {"Authorization": "Bearer test-organizer-token-for-eventflow-api"}


async def event(client, capacity=1):
    response = await client.post(
        "/events",
        headers=AUTH,
        json={
            "title": "Registration test",
            "description": "",
            "capacity": capacity,
            "starts_at": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def register(client, event_id, email, token=None):
    token = token or token_urlsafe(32)
    response = await client.post(
        f"/events/{event_id}/registrations",
        json={"email": email},
        headers={"X-Registration-Token": token},
    )
    assert response.status_code == 200, response.text
    return response.json(), token


async def act(client, record, token, action="cancel"):
    return await client.post(
        f"/registrations/{record['id']}/{action}",
        headers={"Authorization": f"Bearer {token}"},
    )


async def status(client, record, token):
    response = await client.get(
        f"/registrations/{record['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    return response.json()


async def test_registration_duplicate_normalization_and_private_access(
    client, database
):
    eid = await event(client)
    first, token = await register(client, eid, " Person@EXAMPLE.COM ")
    assert first["status"] == "confirmed" and first["email"] == "person@example.com"
    assert first["queue_position"] is None
    retry, _ = await register(client, eid, "person@example.com", token)
    assert retry["id"] == first["id"]
    duplicate = await client.post(
        f"/events/{eid}/registrations",
        json={"email": "PERSON@example.com"},
        headers={"X-Registration-Token": token_urlsafe(32)},
    )
    assert duplicate.status_code == 409
    assert first["id"] not in duplicate.text and token not in duplicate.text
    assert (await client.get(f"/registrations/{first['id']}")).status_code == 401
    wrong = {"Authorization": "Bearer wrong"}
    assert (
        await client.get(f"/registrations/{first['id']}", headers=wrong)
    ).status_code == 404
    assert (
        await client.post(f"/registrations/{first['id']}/cancel", headers=wrong)
    ).status_code == 404
    assert (await client.get(f"/events/{eid}/registrations")).status_code == 401
    listing = await client.get(f"/events/{eid}/registrations", headers=AUTH)
    assert listing.json()["total"] == 1
    assert "token_hash" not in listing.text and token not in listing.text
    async with database.connect() as connection:
        stored = await connection.scalar(text("SELECT token_hash FROM registrations"))
        assert len(stored) == 64 and stored != token


async def test_fifo_cancel_idempotence_and_explicit_rejoin(client):
    eid = await event(client)
    first, secret = await register(client, eid, "one@example.com")
    second, secret2 = await register(client, eid, "two@example.com")
    third, secret3 = await register(client, eid, "three@example.com")
    assert second["queue_position"] == 1 and third["queue_position"] == 2
    assert (await act(client, first, secret)).status_code == 200
    assert (await act(client, first, secret)).status_code == 200
    assert (await status(client, second, secret2))["status"] == "confirmed"
    assert (await status(client, third, secret3))["queue_position"] == 1
    # Replaying the original POST must not silently undo a cancellation.
    replay, _ = await register(client, eid, "one@example.com", secret)
    assert replay["status"] == "cancelled"
    rejoined = await act(client, first, secret, "rejoin")
    assert rejoined.status_code == 200 and rejoined.json()["queue_position"] == 2
    assert rejoined.json()["queue_order"] > third["queue_order"]
    assert (await act(client, second, secret2)).status_code == 200
    assert (await status(client, third, secret3))["status"] == "confirmed"


async def test_cancelling_waiter_does_not_promote_over_capacity(client):
    eid = await event(client)
    first, secret = await register(client, eid, "one@example.com")
    second, secret2 = await register(client, eid, "two@example.com")
    third, secret3 = await register(client, eid, "three@example.com")
    await act(client, second, secret2)
    assert (await status(client, first, secret))["status"] == "confirmed"
    assert (await status(client, third, secret3))["queue_position"] == 1
    availability = (await client.get(f"/events/{eid}/availability")).json()
    assert availability == {
        "capacity": 1,
        "confirmed": 1,
        "waiting": 1,
        "available": 0,
        "registration_open": True,
    }


@pytest.mark.parametrize("count,capacity", [(2, 1), (20, 5)])
async def test_concurrent_registration_never_exceeds_capacity(
    client, database, count, capacity
):
    eid = await event(client, capacity)
    barrier = asyncio.Barrier(count)

    async def submit(index):
        await barrier.wait()
        return await register(client, eid, f"person{index}@example.com")

    results = await asyncio.wait_for(
        asyncio.gather(*(submit(i) for i in range(count))), timeout=30
    )
    records = [record for record, _ in results]
    assert sum(record["status"] == "confirmed" for record in records) == capacity
    assert sum(record["status"] == "waiting" for record in records) == count - capacity
    assert len({record["id"] for record in records}) == count
    assert len({record["queue_order"] for record in records}) == count
    async with database.connect() as connection:
        confirmed = await connection.scalar(
            text("SELECT count(*) FROM registrations WHERE status='confirmed'")
        )
        counter = await connection.scalar(
            text("SELECT confirmed_count FROM events WHERE id=:id"), {"id": eid}
        )
        assert confirmed == counter == capacity


async def test_concurrent_identical_retries_are_idempotent(client):
    eid = await event(client, 5)
    token = token_urlsafe(32)
    barrier = asyncio.Barrier(10)

    async def submit():
        await barrier.wait()
        return await register(client, eid, "same@example.com", token)

    results = await asyncio.wait_for(
        asyncio.gather(*(submit() for _ in range(10))), timeout=30
    )
    assert len({record["id"] for record, _ in results}) == 1
    assert (await client.get(f"/events/{eid}/availability")).json()["confirmed"] == 1


async def test_concurrent_duplicate_email_does_not_disclose_access(client):
    eid = await event(client, 2)
    barrier = asyncio.Barrier(5)

    async def submit():
        await barrier.wait()
        return await client.post(
            f"/events/{eid}/registrations",
            json={"email": "same@example.com"},
            headers={"X-Registration-Token": token_urlsafe(32)},
        )

    responses = await asyncio.wait_for(
        asyncio.gather(*(submit() for _ in range(5))), timeout=30
    )
    assert sorted(response.status_code for response in responses) == [
        200,
        409,
        409,
        409,
        409,
    ]


async def test_simultaneous_cancellations_promote_first_two_only(client):
    eid = await event(client, 2)
    records = [await register(client, eid, f"p{i}@example.com") for i in range(6)]
    results = await asyncio.wait_for(
        asyncio.gather(
            act(client, *records[0]), act(client, *records[1]), act(client, *records[0])
        ),
        timeout=30,
    )
    assert all(result.status_code == 200 for result in results)
    states = [await status(client, record, token) for record, token in records]
    assert [state["status"] for state in states] == [
        "cancelled",
        "cancelled",
        "confirmed",
        "confirmed",
        "waiting",
        "waiting",
    ]


async def test_capacity_rules_and_history_protection(client):
    eid = await event(client)
    first, token = await register(client, eid, "first@example.com")
    second, token2 = await register(client, eid, "second@example.com")
    third, token3 = await register(client, eid, "third@example.com")
    changed = await client.patch(f"/events/{eid}", json={"capacity": 2}, headers=AUTH)
    assert changed.status_code == 200 and changed.json()["confirmed_count"] == 2
    assert (await status(client, second, token2))["status"] == "confirmed"
    assert (await status(client, third, token3))["status"] == "waiting"
    assert (
        await client.patch(f"/events/{eid}", json={"capacity": 1}, headers=AUTH)
    ).status_code == 409
    assert (await client.delete(f"/events/{eid}", headers=AUTH)).status_code == 409
    for record, secret in ((first, token), (second, token2), (third, token3)):
        await act(client, record, secret)
    assert (await client.delete(f"/events/{eid}", headers=AUTH)).status_code == 409


async def test_past_event_and_validation(client, database):
    eid = await event(client)
    first, token = await register(client, eid, "first@example.com")
    async with database.begin() as connection:
        await connection.execute(
            text("UPDATE events SET starts_at=now()-interval '1 day' WHERE id=:id"),
            {"id": eid},
        )
    assert (await act(client, first, token)).status_code == 409
    response = await client.post(
        f"/events/{eid}/registrations",
        json={"email": "new@example.com"},
        headers={"X-Registration-Token": token_urlsafe(32)},
    )
    assert response.status_code == 409
    assert not (await client.get(f"/events/{eid}/availability")).json()[
        "registration_open"
    ]
    assert (
        await client.post(
            f"/events/{eid}/registrations",
            json={"email": "bad"},
            headers={"X-Registration-Token": token_urlsafe(32)},
        )
    ).status_code == 422
    assert (
        await client.post(
            f"/events/{eid}/registrations", json={"email": "a@example.com"}
        )
    ).status_code == 422
    assert (await client.get(f"/events/{uuid4()}/availability")).status_code == 404


async def test_database_enforces_capacity_and_normalized_email_uniqueness(
    client, database
):
    eid = await event(client)
    await register(client, eid, "first@example.com")
    insert_sql = text(
        "INSERT INTO registrations (id,event_id,email,token_hash,status,queue_order) "
        "VALUES (:id,:eid,:email,:hash,'confirmed',:position)"
    )
    with pytest.raises(IntegrityError):
        async with database.begin() as connection:
            await connection.execute(
                insert_sql,
                {
                    "id": uuid4(),
                    "eid": eid,
                    "email": "raw@example.com",
                    "hash": "a" * 64,
                    "position": 100,
                },
            )
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT confirmed_count FROM events WHERE id=:id"), {"id": eid}
            )
            == 1
        )
        assert await connection.scalar(text("SELECT count(*) FROM registrations")) == 1
    with pytest.raises(IntegrityError):
        async with database.begin() as connection:
            await connection.execute(
                text("UPDATE events SET capacity=0 WHERE id=:id"), {"id": eid}
            )


async def test_counter_rolls_back_with_registration(client, database):
    eid = await event(client)
    async with database.connect() as connection:
        transaction = await connection.begin()
        await connection.execute(
            text(
                "INSERT INTO registrations "
                "(id,event_id,email,token_hash,status,queue_order) "
                "VALUES (:id,:eid,'rollback@example.com',:hash,'confirmed',1)"
            ),
            {"id": uuid4(), "eid": eid, "hash": "b" * 64},
        )
        assert (
            await connection.scalar(
                text("SELECT confirmed_count FROM events WHERE id=:id"), {"id": eid}
            )
            == 1
        )
        await transaction.rollback()
        assert (
            await connection.scalar(
                text("SELECT confirmed_count FROM events WHERE id=:id"), {"id": eid}
            )
            == 0
        )


async def test_cancel_racing_new_registration_preserves_fifo(client):
    eid = await event(client)
    first, token = await register(client, eid, "first@example.com")
    waiter, waiter_token = await register(client, eid, "waiter@example.com")
    _, (new, _) = await asyncio.wait_for(
        asyncio.gather(
            act(client, first, token), register(client, eid, "new@example.com")
        ),
        timeout=30,
    )
    assert (await status(client, waiter, waiter_token))["status"] == "confirmed"
    assert new["status"] == "waiting"


async def test_capacity_increase_racing_registration_promotes_existing_waiter(client):
    eid = await event(client)
    await register(client, eid, "first@example.com")
    waiter, token = await register(client, eid, "waiter@example.com")
    response, (new, new_token) = await asyncio.wait_for(
        asyncio.gather(
            client.patch(f"/events/{eid}", json={"capacity": 2}, headers=AUTH),
            register(client, eid, "new@example.com"),
        ),
        timeout=30,
    )
    assert response.status_code == 200
    assert (await status(client, waiter, token))["status"] == "confirmed"
    assert (await status(client, new, new_token))["status"] == "waiting"


async def test_raw_concurrent_inserts_are_still_capacity_constrained(client, database):
    eid = await event(client)
    barrier = asyncio.Barrier(2)

    async def raw_insert(index):
        await barrier.wait()
        try:
            async with database.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO registrations "
                        "(id,event_id,email,token_hash,status,queue_order) "
                        "VALUES (:id,:eid,:email,:hash,'confirmed',:position)"
                    ),
                    {
                        "id": uuid4(),
                        "eid": eid,
                        "email": f"raw{index}@example.com",
                        "hash": str(index) * 64,
                        "position": index,
                    },
                )
            return True
        except IntegrityError:
            return False

    results = await asyncio.wait_for(
        asyncio.gather(raw_insert(1), raw_insert(2)), timeout=30
    )
    assert sorted(results) == [False, True]
    async with database.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM registrations")) == 1
        assert await connection.scalar(text("SELECT confirmed_count FROM events")) == 1


@pytest.mark.parametrize("email", ["same@example.com", "UPPER@example.com"])
async def test_db_enforces_email_uniqueness_and_normalization(client, database, email):
    eid = await event(client)
    await register(client, eid, "same@example.com")
    with pytest.raises(IntegrityError):
        async with database.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO registrations "
                    "(id,event_id,email,token_hash,status,queue_order) "
                    "VALUES (:id,:eid,:email,:hash,'waiting',100)"
                ),
                {"id": uuid4(), "eid": eid, "email": email, "hash": "c" * 64},
            )


async def test_reused_key_different_email_is_rejected(client):
    eid = await event(client, 2)
    _, token = await register(client, eid, "one@example.com")
    response = await client.post(
        f"/events/{eid}/registrations",
        json={"email": "two@example.com"},
        headers={"X-Registration-Token": token},
    )
    assert response.status_code == 409
