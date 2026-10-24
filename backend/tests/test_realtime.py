import asyncio

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_notifications import AUTH, cancel, event, register

from app.api.realtime import revision_snapshot, updates


async def test_two_sse_clients_receive_registration_promotion_checkin_and_reschedule(
    client,
    database,
):
    sessions = async_sessionmaker(database, expire_on_commit=False)
    eid = await event(client)
    streams = [updates(sessions, interval=0.01), updates(sessions, interval=0.01)]

    async def next_update():
        messages = await asyncio.wait_for(
            asyncio.gather(*(anext(stream) for stream in streams)),
            5,
        )
        assert messages[0] == messages[1]
        assert "event: invalidate" in messages[0]
        assert "data: {}" in messages[0]
        return messages[0]

    try:
        for stream in streams:
            assert await anext(stream) == "retry: 2000\n\n"
        previous = await next_update()
        first, token = await register(client, eid)
        current = await next_update()
        assert previous != current and token not in current
        waiter, secret = await register(client, eid, "waiting@example.com")
        assert await next_update() != current
        await cancel(client, first, token)
        promoted = await next_update()
        response = await client.get(
            f"/registrations/{waiter['id']}/ticket",
            headers={"Authorization": f"Bearer {secret}"},
        )
        code = response.json()["code"]
        response = await client.post(
            f"/events/{eid}/check-in", headers=AUTH, json={"code": code}
        )
        assert response.status_code == 200
        checked = await next_update()
        assert checked != promoted and code not in checked
        assert "waiting@example.com" not in checked
        await client.patch(f"/events/{eid}", headers=AUTH, json={"title": "Changed"})
        final = await next_update()
        assert final != checked
        # A new connection always receives an invalidate, even when nothing changed.
        reconnect = updates(sessions, interval=0.01)
        try:
            await anext(reconnect)
            assert await anext(reconnect) == final
        finally:
            await reconnect.aclose()
    finally:
        for stream in streams:
            await stream.aclose()


async def test_uncommitted_and_rolled_back_updates_are_not_published(client, database):
    eid = await event(client)
    sessions = async_sessionmaker(database, expire_on_commit=False)
    before = await revision_snapshot(sessions)
    async with database.connect() as connection:
        transaction = await connection.begin()
        await connection.execute(
            text("UPDATE events SET title='Uncommitted' WHERE id=:id"), {"id": eid}
        )
        assert await revision_snapshot(sessions) == before
        await transaction.rollback()
    assert await revision_snapshot(sessions) == before


async def test_heartbeat_and_database_failure_close_stream(monkeypatch):
    import app.api.realtime as realtime

    async def snapshot(_):
        return "version"

    monkeypatch.setattr(realtime, "revision_snapshot", snapshot)
    stream = updates(None, interval=0)
    await anext(stream)
    assert "invalidate" in await anext(stream)
    assert await anext(stream) == "event: heartbeat\ndata: {}\n\n"

    async def failure(_):
        raise SQLAlchemyError("private connection details")

    monkeypatch.setattr(realtime, "revision_snapshot", failure)
    assert await anext(stream) == "event: unavailable\ndata: {}\n\n"
    try:
        await anext(stream)
        raise AssertionError("Stream must close on database failure")
    except StopAsyncIteration:
        pass
