from datetime import datetime
from secrets import token_hex
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("code", name="uq_tickets_code"),
        CheckConstraint("code ~ '^[0-9A-F]{32}$'", name="ck_tickets_code"),
        CheckConstraint(
            "revoked_at IS NULL OR checked_in_at IS NULL",
            name="ck_tickets_used_not_revoked",
        ),
        Index(
            "uq_tickets_active_registration",
            "registration_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    registration_id: Mapped[UUID] = mapped_column(
        ForeignKey("registrations.id", ondelete="CASCADE")
    )
    code: Mapped[str] = mapped_column(
        String(32),
        default=lambda: token_hex(16).upper(),
        server_default=text("upper(replace(gen_random_uuid()::text, '-', ''))"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
