from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('confirmation','promotion','reminder','rescheduled')",
            name="ck_notifications_kind",
        ),
        CheckConstraint(
            "status IN ('pending','processing','sent','skipped')",
            name="ck_notifications_status",
        ),
        CheckConstraint("attempts >= 0", name="ck_notifications_attempts"),
        Index("ix_notifications_due", "status", "available_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    registration_id: Mapped[UUID] = mapped_column(
        ForeignKey("registrations.id", ondelete="CASCADE")
    )
    ticket_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(16))
    deduplication_key: Mapped[str] = mapped_column(String(160), unique=True)
    schedule_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), server_default="pending")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    lease_token: Mapped[UUID | None]
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(100))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
