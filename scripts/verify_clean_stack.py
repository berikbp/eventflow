"""Verify a fresh isolated Compose project; never touches the normal stack.

Python 3.12+ standard library only. Creates a unique project/volume and random
loopback ports, uses a private generated env file, and removes that project's
containers, network and volume in finally. Docker build cache is allowed.
"""

import argparse
import concurrent.futures
import json
import os
import secrets
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def request(base, path, *, data=None, method=None, token=None, key=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["X-Registration-Token"] = key
    query = urllib.request.Request(
        base + path,
        headers=headers,
        data=json.dumps(data).encode() if data is not None else None,
        method=method or ("POST" if data is not None else "GET"),
    )
    try:
        response = urllib.request.urlopen(query, timeout=15)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        assert response.status == expected, f"{query.method} {path}: {response.status}"
        body = response.read()
        return json.loads(body) if body else None


def wait_until(check, timeout=45):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            value = check()
            if value:
                return value
        except (OSError, AssertionError):
            pass
        time.sleep(0.5)
    raise AssertionError("Timed out waiting for isolated stack state")


def sse_event(response):
    lines = []
    while True:
        raw = response.readline()
        if not raw:
            raise AssertionError("SSE ended unexpectedly")
        line = raw.decode().strip()
        if not line:
            if any(item.startswith("event:") for item in lines):
                return "\n".join(lines)
            lines = []
        else:
            lines.append(line)
        if response.closed:
            raise AssertionError("SSE closed unexpectedly")


def verify(compose, ports, token, report):
    api = f"http://127.0.0.1:{ports['FRONTEND_PORT']}/api"
    mail = f"http://127.0.0.1:{ports['MAILPIT_HTTP_PORT']}"
    wait_until(lambda: request(api, "/health/ready")["database"] == "ok")
    assert request(api, "/events")["total"] == 0
    compose("exec", "-T", "backend", "/app/.venv/bin/python", "-m", "app.seed")
    compose("exec", "-T", "backend", "/app/.venv/bin/python", "-m", "app.seed")
    assert request(api, "/events")["total"] == 2
    compose("exec", "-T", "backend", "/app/.venv/bin/alembic", "check")
    report["empty_database_migrations_and_seed"] = "passed"

    def db(query, parameters=None):
        program = (
            "import asyncio,json,os,sys; "
            "from sqlalchemy import text; "
            "from sqlalchemy.ext.asyncio import create_async_engine; "
            "exec('async def main():\\n"
            ' engine=create_async_engine(os.environ["DATABASE_URL"])\\n'
            " try:\\n"
            "  async with engine.connect() as c:\\n"
            "   r=await c.execute(text(sys.argv[1]),json.loads(sys.argv[2]))\\n"
            "   print(json.dumps([dict(x) for x in r.mappings()]))\\n"
            " finally: await engine.dispose()'); asyncio.run(main())"
        )
        return json.loads(
            compose(
                "exec",
                "-T",
                "backend",
                "/app/.venv/bin/python",
                "-c",
                program,
                query,
                json.dumps(parameters or {}),
                capture=True,
            )
        )

    starts = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    event = request(
        api,
        "/events",
        data={
            "title": "Isolated Phase 6 verification",
            "capacity": 5,
            "starts_at": starts,
        },
        token=token,
        expected=201,
    )
    eid = event["id"]
    stream1 = urllib.request.urlopen(api + "/updates", timeout=10)
    stream2 = urllib.request.urlopen(api + "/updates", timeout=10)
    try:
        initial = sse_event(stream1)
        assert initial == sse_event(stream2)
        assert "event: invalidate" in initial
        attempts = [
            (f"clean-{i}@example.com", secrets.token_urlsafe(32)) for i in range(20)
        ]

        def register(attempt):
            email, key = attempt
            result = request(
                api, f"/events/{eid}/registrations", data={"email": email}, key=key
            )
            return result, key

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            records = list(pool.map(register, attempts))
        confirmed = [pair for pair in records if pair[0]["status"] == "confirmed"]
        waiting = sorted(
            [pair for pair in records if pair[0]["status"] == "waiting"],
            key=lambda pair: pair[0]["queue_order"],
        )
        assert len(confirmed) == 5 and len(waiting) == 15
        assert len({record["id"] for record, _ in records}) == 20
        assert sse_event(stream1) != initial
        assert sse_event(stream2) != initial
        report["concurrent_registration"] = {
            "requests": 20,
            "confirmed": 5,
            "waiting": 15,
        }
        report["two_sse_clients"] = "passed"
    finally:
        stream1.close()
        stream2.close()

    first, key = confirmed[0]
    retried = request(
        api, f"/events/{eid}/registrations", data={"email": first["email"]}, key=key
    )
    assert retried["id"] == first["id"]
    old = request(api, f"/registrations/{first['id']}/ticket", token=key)
    request(api, f"/registrations/{first['id']}/cancel", method="POST", token=key)
    promoted, promoted_key = waiting[0]
    ticket = request(api, f"/registrations/{promoted['id']}/ticket", token=promoted_key)
    assert ticket and ticket["code"] != old["code"]
    request(
        api,
        f"/events/{eid}/check-in",
        data={"code": old["code"]},
        token=token,
        expected=409,
    )
    first_entry = request(
        api, f"/events/{eid}/check-in", data={"code": ticket["code"]}, token=token
    )
    second_entry = request(
        api, f"/events/{eid}/check-in", data={"code": ticket["code"]}, token=token
    )
    assert not first_entry["already_checked_in"] and second_entry["already_checked_in"]
    assert (
        first_entry["ticket"]["checked_in_at"]
        == second_entry["ticket"]["checked_in_at"]
    )
    request(
        api,
        f"/registrations/{promoted['id']}/cancel",
        method="POST",
        token=promoted_key,
        expected=409,
    )
    report["fifo_tickets_revocation_and_single_use_checkin"] = "passed"

    moved = request(
        api,
        f"/events/{eid}",
        method="PATCH",
        token=token,
        data={
            "starts_at": (datetime.now(UTC) + timedelta(hours=12)).isoformat(),
        },
    )
    assert moved["schedule_version"] == 2
    wait_until(
        lambda: db(
            "SELECT kind FROM notifications WHERE event_id=:id AND status='sent' "
            "AND kind='reminder'",
            {"id": eid},
        )
    )
    messages = request(mail, "/api/v1/messages?limit=200")["messages"]
    assert any("Напоминание" in message["Subject"] for message in messages)
    report["reschedule_and_real_mailpit_reminder"] = "passed"

    # Inject SMTP outage in this project only; HTTP registration must still work.
    compose("stop", "mailpit")
    retry_event = request(
        api,
        "/events",
        data={
            "title": "SMTP failure recovery",
            "capacity": 1,
            "starts_at": starts,
        },
        token=token,
        expected=201,
    )
    retry = request(
        api,
        f"/events/{retry_event['id']}/registrations",
        data={"email": "smtp-recovery@example.com"},
        key=secrets.token_urlsafe(32),
    )
    query = (
        "SELECT status,attempts FROM notifications WHERE registration_id=:id "
        "AND kind='confirmation'"
    )
    wait_until(
        lambda: any(
            row["attempts"] >= 1 and row["status"] == "pending"
            for row in db(query, {"id": retry["id"]})
        )
    )
    compose("start", "mailpit")
    wait_until(
        lambda: any(row["status"] == "sent" for row in db(query, {"id": retry["id"]}))
    )
    report["smtp_outage_retry"] = "passed"

    # Verify non-health API failure too, then recover persisted data/jobs.
    compose("stop", "db")
    assert request(api, "/events", expected=503)["detail"].startswith("База данных")
    assert (
        request(api, "/health/ready", expected=503)["detail"] == "Database unavailable"
    )
    compose("start", "db")
    compose("restart", "backend", "worker")
    wait_until(lambda: request(api, "/health/ready")["status"] == "ok")
    counts = request(api, f"/events/{eid}/availability")
    assert (
        counts["confirmed"] == 5
        and counts["waiting"] == 14
        and counts["checked_in"] == 1
    )
    saved = request(api, f"/registrations/{promoted['id']}/ticket", token=promoted_key)
    assert saved["checked_in_at"] == first_entry["ticket"]["checked_in_at"]
    compose("exec", "-T", "backend", "/app/.venv/bin/alembic", "check")
    report["database_outage_and_restart_persistence"] = "passed"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report", type=Path, default=Path("/tmp/eventflow-clean-stack-report.json")
    )
    args = parser.parse_args()
    project = "eventflow-verify-" + uuid4().hex[:12]
    report = {
        "started_at": datetime.now(UTC).isoformat(),
        "project": project,
        "scope": "fresh containers and PostgreSQL volume; Docker build cache allowed",
        "status": "running",
    }
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=project + "-") as directory:
        envfile = Path(directory) / "stack.env"
        reservations = [socket.socket() for _ in range(5)]
        for sock in reservations:
            sock.bind(("127.0.0.1", 0))
        ports = dict(
            zip(
                [
                    "POSTGRES_PORT",
                    "API_PORT",
                    "FRONTEND_PORT",
                    "MAILPIT_HTTP_PORT",
                    "MAILPIT_SMTP_PORT",
                ],
                [sock.getsockname()[1] for sock in reservations],
                strict=True,
            )
        )
        token = secrets.token_urlsafe(48)
        envfile.write_text(
            "\n".join(
                f"{key}={value}"
                for key, value in {
                    **ports,
                    "POSTGRES_USER": "eventflow",
                    "POSTGRES_PASSWORD": "verify_local",
                    "POSTGRES_DB": "eventflow",
                    "ORGANIZER_TOKEN": token,
                    "PUBLIC_BASE_URL": f"http://127.0.0.1:{ports['FRONTEND_PORT']}",
                }.items()
            )
            + "\n"
        )
        envfile.chmod(0o600)
        for sock in reservations:
            sock.close()
        environment = os.environ.copy()
        for key in [
            *ports,
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "ORGANIZER_TOKEN",
            "PUBLIC_BASE_URL",
            "COMPOSE_PROJECT_NAME",
            "COMPOSE_FILE",
        ]:
            environment.pop(key, None)
        command = [
            "docker",
            "compose",
            "--project-name",
            project,
            "--env-file",
            str(envfile),
            "-f",
            str(ROOT / "compose.yaml"),
        ]

        def compose(*parts, capture=False):
            completed = subprocess.run(
                command + list(parts),
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode:
                # Output contains no generated env/token, but can include Docker errors.
                raise RuntimeError(completed.stderr[-3000:] or "Compose command failed")
            if capture:
                return completed.stdout.strip()
            print("Compose:", " ".join(parts[:4]), "passed", flush=True)
            return None

        try:
            compose("up", "--build", "-d", "--wait", "--wait-timeout", "120")
            verify(compose, ports, token, report)
            report["status"] = "passed"
        except Exception as exc:
            report["status"] = "failed"
            report["error"] = str(exc)
            raise
        finally:
            try:
                compose("down", "--volumes", "--remove-orphans")
                report["cleanup"] = (
                    "passed: only the unique verification project removed"
                )
            except (OSError, RuntimeError):
                report["cleanup"] = "failed: inspect the reported verification project"
                report["status"] = "failed"
            report["finished_at"] = datetime.now(UTC).isoformat()
            report["duration_seconds"] = round(time.monotonic() - started, 2)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            )
    if report["status"] != "passed":
        raise SystemExit(1)
    print("Fresh isolated stack verification passed; report:", args.report)


if __name__ == "__main__":
    main()
