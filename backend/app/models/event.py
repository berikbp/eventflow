from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "capacity > 0 AND capacity <= 1000000", name="ck_events_capacity"
        ),
        CheckConstraint("length(trim(title)) > 0", name="ck_events_title"),
        Index("ix_events_starts_at_id", "starts_at", "id"),
        CheckConstraint(
            "confirmed_count >= 0 AND confirmed_count <= capacity",
            name="ck_events_confirmed_count",
        ),
        CheckConstraint(
            "next_registration_order >= 0", name="ck_events_registration_order"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    confirmed_count: Mapped[int] = mapped_column(Integer, server_default="0")
    next_registration_order: Mapped[int] = mapped_column(BigInteger, server_default="0")
    revision: Mapped[int] = mapped_column(BigInteger, server_default="1")
    schedule_version: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
