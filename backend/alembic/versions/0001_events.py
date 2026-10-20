"""Create events table."""

import sqlalchemy as sa

from alembic import op

revision = "0001_events"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("schedule_version", sa.Integer(), server_default="1", nullable=False),
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
        sa.CheckConstraint(
            "capacity > 0 AND capacity <= 1000000", name="ck_events_capacity"
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_events_title"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_starts_at_id", "events", ["starts_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_events_starts_at_id", table_name="events")
    op.drop_table("events")
