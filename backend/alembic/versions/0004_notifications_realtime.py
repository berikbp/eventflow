"""Durable notification outbox and transactionally updated SSE revisions."""

import sqlalchemy as sa

from alembic import op

revision = "0004_notifications_realtime"
down_revision = "0003_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("revision", sa.BigInteger(), server_default="1", nullable=False),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "event_id",
            sa.Uuid(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "registration_id",
            sa.Uuid(),
            sa.ForeignKey("registrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ticket_id", sa.Uuid(), sa.ForeignKey("tickets.id", ondelete="CASCADE")
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("deduplication_key", sa.String(160), nullable=False, unique=True),
        sa.Column("schedule_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lease_token", sa.Uuid()),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.String(100)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('confirmation','promotion','reminder','rescheduled')",
            name="ck_notifications_kind",
        ),
        sa.CheckConstraint(
            "status IN ('pending','processing','sent','skipped')",
            name="ck_notifications_status",
        ),
        sa.CheckConstraint("attempts >= 0", name="ck_notifications_attempts"),
    )
    op.create_index("ix_notifications_due", "notifications", ["status", "available_at"])
    op.execute("""
        CREATE FUNCTION bump_event_revision() RETURNS trigger AS $$
        BEGIN
            NEW.revision := OLD.revision + 1;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER event_revision BEFORE UPDATE ON events
        FOR EACH ROW EXECUTE FUNCTION bump_event_revision();
    """)
    op.execute("""
        CREATE FUNCTION registration_revision() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                UPDATE events SET revision = revision + 1 WHERE id = OLD.event_id;
                RETURN OLD;
            END IF;
            UPDATE events SET revision = revision + 1 WHERE id = NEW.event_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER registration_revision AFTER INSERT OR UPDATE OR DELETE
        ON registrations FOR EACH ROW EXECUTE FUNCTION registration_revision();
    """)
    op.execute("""
        CREATE FUNCTION ticket_revision() RETURNS trigger AS $$
        DECLARE rid uuid;
        BEGIN
            IF TG_OP = 'DELETE' THEN rid := OLD.registration_id;
            ELSE rid := NEW.registration_id;
            END IF;
            UPDATE events SET revision = revision + 1 WHERE id =
                (SELECT event_id FROM registrations WHERE id = rid);
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER ticket_revision AFTER INSERT OR UPDATE OR DELETE
        ON tickets FOR EACH ROW EXECUTE FUNCTION ticket_revision();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER ticket_revision ON tickets")
    op.execute("DROP FUNCTION ticket_revision()")
    op.execute("DROP TRIGGER registration_revision ON registrations")
    op.execute("DROP FUNCTION registration_revision()")
    op.execute("DROP TRIGGER event_revision ON events")
    op.execute("DROP FUNCTION bump_event_revision()")
    op.drop_table("notifications")
    op.drop_column("events", "revision")
