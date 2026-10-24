"""Tickets, unique active issuance, and backfill for Phase 3 confirmations."""

import sqlalchemy as sa

from alembic import op

revision = "0003_tickets"
down_revision = "0002_registrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "registration_id",
            sa.Uuid(),
            sa.ForeignKey("registrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(32),
            server_default=sa.text("upper(replace(gen_random_uuid()::text, '-', ''))"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_tickets_code"),
        sa.CheckConstraint("code ~ '^[0-9A-F]{32}$'", name="ck_tickets_code"),
        sa.CheckConstraint(
            "revoked_at IS NULL OR checked_in_at IS NULL",
            name="ck_tickets_used_not_revoked",
        ),
    )
    op.create_index(
        "uq_tickets_active_registration",
        "tickets",
        ["registration_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.execute("""
        INSERT INTO tickets (id, registration_id)
        SELECT gen_random_uuid(), id FROM registrations WHERE status = 'confirmed'
    """)


def downgrade() -> None:
    op.drop_table("tickets")
