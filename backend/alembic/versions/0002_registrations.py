"""Registrations, FIFO order and transactionally enforced seat counter."""

import sqlalchemy as sa

from alembic import op

revision = "0002_registrations"
down_revision = "0001_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("confirmed_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "events",
        sa.Column(
            "next_registration_order",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_events_confirmed_count",
        "events",
        "confirmed_count >= 0 AND confirmed_count <= capacity",
    )
    op.create_check_constraint(
        "ck_events_registration_order", "events", "next_registration_order >= 0"
    )
    op.create_table(
        "registrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_id",
            sa.Uuid(),
            sa.ForeignKey("events.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("queue_order", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "email", name="uq_registrations_event_email"),
        sa.UniqueConstraint(
            "event_id", "token_hash", name="uq_registrations_event_token"
        ),
        sa.UniqueConstraint(
            "event_id", "queue_order", name="uq_registrations_event_order"
        ),
        sa.CheckConstraint(
            "status IN ('confirmed','waiting','cancelled')",
            name="ck_registration_status",
        ),
        sa.CheckConstraint("email = lower(btrim(email))", name="ck_registration_email"),
        sa.CheckConstraint("queue_order > 0", name="ck_registration_order"),
    )
    op.create_index(
        "ix_registrations_queue", "registrations", ["event_id", "status", "queue_order"]
    )
    op.execute("""
        CREATE FUNCTION maintain_registration_seats() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                IF NEW.event_id <> OLD.event_id THEN
                    RAISE EXCEPTION 'Registration event cannot change'
                        USING ERRCODE = '23514';
                END IF;
                IF NEW.status = OLD.status THEN
                    RETURN NEW;
                END IF;
            END IF;
            IF TG_OP <> 'INSERT' THEN
                IF OLD.status = 'confirmed' THEN
                    UPDATE events SET confirmed_count = confirmed_count - 1
                        WHERE id = OLD.event_id;
                END IF;
            END IF;
            IF TG_OP <> 'DELETE' THEN
                IF NEW.status = 'confirmed' THEN
                    UPDATE events SET confirmed_count = confirmed_count + 1
                        WHERE id = NEW.event_id;
                END IF;
                RETURN NEW;
            END IF;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER registration_seats
        AFTER INSERT OR UPDATE OR DELETE ON registrations
        FOR EACH ROW EXECUTE FUNCTION maintain_registration_seats()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER registration_seats ON registrations")
    op.execute("DROP FUNCTION maintain_registration_seats()")
    op.drop_table("registrations")
    op.drop_constraint("ck_events_registration_order", "events", type_="check")
    op.drop_constraint("ck_events_confirmed_count", "events", type_="check")
    op.drop_column("events", "next_registration_order")
    op.drop_column("events", "confirmed_count")
