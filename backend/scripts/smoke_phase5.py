"""Live Mailpit/restart smoke. Run from backend; see docs/testing.md.

prepare requires the worker to be stopped. verify checks delivery and cleans up
only the event recorded in the private state file. No secrets are printed.
"""

import argparse
import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "verify", "cleanup-browser"])
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    engine = create_async_engine(str(settings.database_url))
    try:
        if args.mode == "cleanup-browser":
            states = json.loads(args.state.read_text())
            if not isinstance(states, list):
                states = [states]
            async with engine.begin() as connection:
                for state in states:
                    title = await connection.scalar(
                        text("SELECT title FROM events WHERE id=:id FOR UPDATE"),
                        {"id": state["eid"]},
                    )
                    if title is None:
                        continue
                    assert title in {
                        "Phase 5 browser smoke",
                        "Phase 5 updated live",
                        "Phase 5 reconnected",
                        "Phase 6 " + "x" * 190,
                    }
                    await connection.execute(
                        text("DELETE FROM registrations WHERE event_id=:id"),
                        {"id": state["eid"]},
                    )
                    await connection.execute(
                        text("DELETE FROM events WHERE id=:id"),
                        {"id": state["eid"]},
                    )
            args.state.unlink()
            print("Removed only recorded browser smoke events and their registrations")
            return
        async with httpx.AsyncClient(timeout=15) as client:
            if args.mode == "prepare":
                if args.state.exists():
                    raise RuntimeError(
                        "State file exists; verify/clean up that run first"
                    )
                marker = uuid4().hex
                email = f"phase5-{marker}@example.com"
                title = f"Phase 5 persistence smoke {marker}"
                response = await client.post(
                    "http://127.0.0.1:5173/api/events",
                    headers={
                        "Authorization": "Bearer "
                        + settings.organizer_token.get_secret_value()
                    },
                    json={
                        "title": title,
                        "capacity": 1,
                        "starts_at": (
                            datetime.now(UTC) + timedelta(hours=12)
                        ).isoformat(),
                    },
                )
                response.raise_for_status()
                eid = response.json()["id"]
                state = {"eid": eid, "title": title, "email": email}
                with args.state.open("x", encoding="utf8") as output:
                    args.state.chmod(0o600)
                    json.dump(state, output)
                response = await client.post(
                    f"http://127.0.0.1:5173/api/events/{eid}/registrations",
                    headers={"X-Registration-Token": token_urlsafe(32)},
                    json={"email": email},
                )
                response.raise_for_status()
                async with engine.connect() as connection:
                    rows = (
                        (
                            await connection.execute(
                                text(
                                    "SELECT status FROM notifications "
                                    "WHERE event_id=:id"
                                ),
                                {"id": eid},
                            )
                        )
                        .scalars()
                        .all()
                    )
                    assert rows == ["pending", "pending"], rows
                print(
                    "Prepared two durable pending jobs; restart services, then verify"
                )
                return
            state = json.loads(args.state.read_text())
            for _ in range(60):
                async with engine.connect() as connection:
                    rows = (
                        (
                            await connection.execute(
                                text(
                                    "SELECT status FROM notifications "
                                    "WHERE event_id=:id"
                                ),
                                {"id": state["eid"]},
                            )
                        )
                        .scalars()
                        .all()
                    )
                if len(rows) == 2 and all(status == "sent" for status in rows):
                    break
                await asyncio.sleep(0.5)
            else:
                raise AssertionError(f"Expected two sent jobs, got {rows}")
            response = await client.get(
                "http://127.0.0.1:8025/api/v1/messages?limit=200"
            )
            response.raise_for_status()
            messages = [
                item
                for item in response.json()["messages"]
                if any(
                    recipient["Address"] == state["email"] for recipient in item["To"]
                )
            ]
            assert len(messages) == 2, (
                f"Expected 2 physical emails, got {len(messages)}"
            )
            assert any("подтверждена" in item["Subject"] for item in messages)
            assert any("Напоминание" in item["Subject"] for item in messages)
            for item in messages:
                response = await client.get(
                    f"http://127.0.0.1:8025/api/v1/message/{item['ID']}"
                )
                response.raise_for_status()
                assert "Код билета:" in response.json()["Text"]
            if not args.keep:
                async with engine.begin() as connection:
                    title = await connection.scalar(
                        text("SELECT title FROM events WHERE id=:id FOR UPDATE"),
                        {"id": state["eid"]},
                    )
                    assert title == state["title"]
                    await connection.execute(
                        text("DELETE FROM registrations WHERE event_id=:id"),
                        {"id": state["eid"]},
                    )
                    await connection.execute(
                        text("DELETE FROM events WHERE id=:id"), {"id": state["eid"]}
                    )
                args.state.unlink()
            print(
                "Verified two sent jobs and two Mailpit emails with tickets; "
                "no duplicates"
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
