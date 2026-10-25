import asyncio
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import Settings
from app.models.notification import Notification
from app.services.notifications import schedule_reminders
from app.worker import claim, deliver_one

AUTH = {"Authorization": "Bearer test-organizer-token-for-eventflow-api"}


def settings():
    return Settings(
        _env_file=None, database_url="postgresql+asyncpg://test:test@localhost/test"
    )


async def event(client, hours=72):
    response = await client.post(
        "/events",
        headers=AUTH,
        json={
            "title": "Outbox test",
            "capacity": 1,
            "starts_at": (datetime.now(UTC) + timedelta(hours=hours)).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def register(client, eid, email="person@example.com", token=None):
    token = token or token_urlsafe(32)
    response = await client.post(
        f"/events/{eid}/registrations",
        json={"email": email},
        headers={"X-Registration-Token": token},
    )
    assert response.status_code == 200, response.text
    return response.json(), token


async def cancel(client, record, token, action="cancel"):
    response = await client.post(
        f"/registrations/{record['id']}/{action}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


async def jobs(database):
    async with async_sessionmaker(database)() as session:
        return (await session.scalars(select(Notification))).all()


async def drain(database):
    sent = []

    async def sender(message, config):
        sent.append(message)

    sessions = async_sessionmaker(database, expire_on_commit=False)
    # A skipped stale job is progress too: continue checking due jobs.
    for _ in range(12):
        await deliver_one(sessions, settings(), sender)
    return sent


async def reschedule(client, eid, hours):
    date = (datetime.now(UTC) + timedelta(hours=hours)).isoformat()
    response = await client.patch(
        f"/events/{eid}", headers=AUTH, json={"starts_at": date}
    )
    assert response.status_code == 200
    return date


async def test_confirmation_retry_is_one_logical_notification(client, database):
    eid = await event(client)
    _, token = await register(client, eid)
    await register(client, eid, token=token)
    assert sorted(job.kind for job in await jobs(database)) == [
        "confirmation",
        "reminder",
    ]
    sent = await drain(database)
    assert len(sent) == 1 and sent[0]["To"] == "person@example.com"
    assert "Код билета:" in sent[0].get_content()
    assert token not in sent[0].get_content()
    assert await drain(database) == []


async def test_waiting_promotion_and_revoked_jobs(client, database):
    eid = await event(client, 12)
    first, token = await register(client, eid, "first@example.com")
    await register(client, eid, "second@example.com")
    assert len(await jobs(database)) == 2
    await cancel(client, first, token)
    sent = await drain(database)
    assert len(sent) == 2  # promotion and immediate reminder
    assert all(message["To"] == "second@example.com" for message in sent)
    assert any("из листа ожидания" in str(message["Subject"]) for message in sent)
    assert {job.status for job in await jobs(database)} == {"sent", "skipped"}


async def test_outbox_rolls_back_with_registration(client, database, monkeypatch):
    from app.services import notifications

    original = notifications.enqueue

    async def fail(session, event, registration, kind, **kwargs):
        if kind == "reminder":
            raise RuntimeError("simulated outbox write failure")
        await original(session, event, registration, kind, **kwargs)

    monkeypatch.setattr(notifications, "enqueue", fail)
    eid = await event(client)
    with pytest.raises(RuntimeError, match="simulated"):
        await register(client, eid)
    async with database.connect() as connection:
        for table in ("registrations", "tickets", "notifications"):
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
        assert await connection.scalar(text("SELECT confirmed_count FROM events")) == 0


async def test_smtp_retry_preserves_identity_and_backoff(client, database):
    eid = await event(client)
    await register(client, eid)
    sessions = async_sessionmaker(database, expire_on_commit=False)
    seen = []

    async def failing(message, config):
        seen.append(message["Message-ID"])
        raise OSError("sensitive SMTP details must not be persisted")

    assert await deliver_one(sessions, settings(), failing)
    entry = next(job for job in await jobs(database) if job.kind == "confirmation")
    assert entry.status == "pending" and entry.attempts == 1
    assert entry.last_error == "OSError" and entry.available_at > datetime.now(UTC)
    assert not await deliver_one(sessions, settings(), failing)
    async with database.begin() as connection:
        await connection.execute(
            text(
                "UPDATE notifications SET available_at=now() WHERE kind='confirmation'"
            )
        )

    async def success(message, config):
        seen.append(message["Message-ID"])

    assert await deliver_one(sessions, settings(), success)
    assert seen[0] == seen[1]
    entry = next(job for job in await jobs(database) if job.kind == "confirmation")
    assert entry.status == "sent" and entry.attempts == 2 and entry.sent_at


async def test_expired_claim_survives_worker_restart(client, database):
    eid = await event(client)
    await register(client, eid)
    sessions = async_sessionmaker(database, expire_on_commit=False)
    first = await claim(sessions, settings())
    assert first and await claim(sessions, settings()) is None
    async with database.begin() as connection:
        await connection.execute(
            text(
                "UPDATE notifications SET lease_until=now()-interval '1 second' "
                "WHERE status='processing'"
            )
        )
    replacement = await claim(
        async_sessionmaker(database, expire_on_commit=False), settings()
    )
    assert replacement.id == first.id
    assert replacement.lease_token != first.lease_token
    assert replacement.message["Message-ID"] == first.message["Message-ID"]


async def test_reminder_once_and_reschedule_replaces_old_jobs(client, database):
    eid = await event(client)
    await register(client, eid)
    assert len(await drain(database)) == 1  # only confirmation is due
    date = await reschedule(client, eid, 12)
    repeated = await client.patch(
        f"/events/{eid}", headers=AUTH, json={"starts_at": date}
    )
    assert repeated.json()["schedule_version"] == 2
    sessions = async_sessionmaker(database, expire_on_commit=False)
    async with sessions.begin() as session:
        await schedule_reminders(session)
        await schedule_reminders(session)
    assert len([job for job in await jobs(database) if job.kind == "reminder"]) == 2
    async with database.begin() as connection:
        await connection.execute(
            text("UPDATE notifications SET available_at=now() WHERE kind='reminder'")
        )
    sent = await drain(database)
    assert len(sent) == 2  # latest reschedule and immediate reminder
    assert sum("Напоминание" in str(message["Subject"]) for message in sent) == 1
    assert all(date[:16] in message.get_content() for message in sent)
    assert await drain(database) == []
    entries = await jobs(database)
    assert (
        next(
            j for j in entries if j.kind == "reminder" and j.schedule_version == 1
        ).status
        == "skipped"
    )
    assert (
        next(
            j for j in entries if j.kind == "reminder" and j.schedule_version == 2
        ).status
        == "sent"
    )


async def test_reschedule_includes_waiting_excludes_cancelled(client, database):
    eid = await event(client)
    await register(client, eid, "confirmed@example.com")
    await register(client, eid, "waiting@example.com")
    record, token = await register(client, eid, "cancelled@example.com")
    await cancel(client, record, token)
    await reschedule(client, eid, 80)
    await reschedule(client, eid, 90)
    changed = [m for m in await drain(database) if "изменилось" in str(m["Subject"])]
    assert len(changed) == 2
    assert {m["To"] for m in changed} == {
        "confirmed@example.com",
        "waiting@example.com",
    }
    assert all(
        "Код билета:" not in m.get_content()
        for m in changed
        if m["To"] == "waiting@example.com"
    )


async def test_reminder_skips_started_event(client, database):
    eid = await event(client, 1)
    await register(client, eid)
    async with database.begin() as connection:
        await connection.execute(
            text("UPDATE events SET starts_at=now()-interval '1 second'")
        )
    sent = await drain(database)
    assert len(sent) == 1 and "подтверждена" in str(sent[0]["Subject"])
    assert (
        next(j for j in await jobs(database) if j.kind == "reminder").status
        == "skipped"
    )


async def test_scheduler_backfill_and_concurrent_deduplication(client, database):
    eid = await event(client, 12)
    await register(client, eid)
    async with database.begin() as connection:
        await connection.execute(text("DELETE FROM notifications"))
    sessions = async_sessionmaker(database, expire_on_commit=False)

    async def schedule():
        async with sessions.begin() as session:
            await schedule_reminders(session)

    await asyncio.gather(schedule(), schedule())
    assert len(await jobs(database)) == 1
    assert len(await drain(database)) == 1


async def test_smtp_holds_no_business_lock(client, database):
    eid = await event(client)
    await register(client, eid)
    sending, release = asyncio.Event(), asyncio.Event()

    async def sender(message, config):
        sending.set()
        await release.wait()

    sessions = async_sessionmaker(database, expire_on_commit=False)
    task = asyncio.create_task(deliver_one(sessions, settings(), sender))
    try:
        await asyncio.wait_for(sending.wait(), 5)
        record, _ = await asyncio.wait_for(
            register(client, eid, "second@example.com"), 5
        )
        assert record["status"] == "waiting"
        await asyncio.wait_for(reschedule(client, eid, 90), 5)
    finally:
        release.set()
        await task


async def test_concurrent_workers_do_not_duplicate_claim(client, database):
    eid = await event(client)
    await register(client, eid)
    seen = []

    async def sender(message, config):
        seen.append(message["Message-ID"])
        await asyncio.sleep(0.01)

    sessions = async_sessionmaker(database, expire_on_commit=False)
    await asyncio.gather(*(deliver_one(sessions, settings(), sender) for _ in range(5)))
    assert len(seen) == 1
    assert (
        next(j for j in await jobs(database) if j.kind == "confirmation").attempts == 1
    )


async def test_rejoin_revives_skipped_reminder_but_never_repeats_sent_one(
    client, database
):
    eid = await event(client, 12)
    record, token = await register(client, eid)
    await cancel(client, record, token)
    assert await drain(database) == []
    await cancel(client, record, token, "rejoin")
    assert len(await drain(database)) == 2  # new confirmation + revived reminder
    await cancel(client, record, token)
    await cancel(client, record, token, "rejoin")
    assert (
        len(await drain(database)) == 1
    )  # new ticket, same schedule reminder already sent
    reminders = [j for j in await jobs(database) if j.kind == "reminder"]
    assert len(reminders) == 1 and reminders[0].status == "sent"


async def test_new_schedule_gets_one_new_reminder_after_previous_was_sent(
    client, database
):
    eid = await event(client, 12)
    await register(client, eid)
    assert len(await drain(database)) == 2
    await reschedule(client, eid, 6)
    sent = await drain(database)
    assert len(sent) == 2
    assert sum("Напоминание" in str(m["Subject"]) for m in sent) == 1
    assert await drain(database) == []


async def test_reschedule_later_postpones_due_reminder(client, database):
    eid = await event(client, 12)
    await register(client, eid)
    await reschedule(client, eid, 96)
    sent = await drain(database)
    assert len(sent) == 2  # confirmation and reschedule; no stale immediate reminder
    assert not any("Напоминание" in str(m["Subject"]) for m in sent)
    reminders = [j for j in await jobs(database) if j.kind == "reminder"]
    assert next(j for j in reminders if j.schedule_version == 1).status == "skipped"
    new = next(j for j in reminders if j.schedule_version == 2)
    assert new.status == "pending"
    assert new.due_at > datetime.now(UTC) + timedelta(hours=71)


async def test_locked_event_does_not_starve_other_events(client, database):
    first = await event(client)
    await register(client, first, "busy@example.com")
    second = await event(client)
    await register(client, second, "ready@example.com")
    sessions = async_sessionmaker(database, expire_on_commit=False)
    async with database.begin() as connection:
        await connection.execute(
            text("SELECT id FROM events WHERE id=:id FOR UPDATE"), {"id": first}
        )
        delivery = await asyncio.wait_for(claim(sessions, settings()), 5)
        assert delivery is not None
        assert delivery.message["To"] == "ready@example.com"


async def test_expired_worker_cannot_overwrite_new_owner_ack(client, database):
    eid = await event(client)
    await register(client, eid)
    sessions = async_sessionmaker(database, expire_on_commit=False)
    sending, release = asyncio.Event(), asyncio.Event()

    async def old_sender(message, config):
        sending.set()
        await release.wait()
        raise OSError("Late failure from expired worker")

    old = asyncio.create_task(deliver_one(sessions, settings(), old_sender))
    try:
        await asyncio.wait_for(sending.wait(), 5)
        async with database.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE notifications SET lease_until=now()-interval '1 second' "
                    "WHERE status='processing'"
                )
            )

        async def replacement_sender(message, config):
            return None

        assert await deliver_one(sessions, settings(), replacement_sender)
    finally:
        release.set()
        await old
    confirmation = next(j for j in await jobs(database) if j.kind == "confirmation")
    assert confirmation.status == "sent" and confirmation.attempts == 2
    assert confirmation.last_error is None
