from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("event_id", "email", name="uq_registrations_event_email"),
        UniqueConstraint("event_id", "token_hash", name="uq_registrations_event_token"),
        UniqueConstraint(
            "event_id", "queue_order", name="uq_registrations_event_order"
        ),
        CheckConstraint(
            "status IN ('confirmed','waiting','cancelled')",
            name="ck_registration_status",
        ),
        CheckConstraint("email = lower(btrim(email))", name="ck_registration_email"),
        CheckConstraint("queue_order > 0", name="ck_registration_order"),
        Index("ix_registrations_queue", "event_id", "status", "queue_order"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT"))
    email: Mapped[str] = mapped_column(String(254))
    token_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    queue_order: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
