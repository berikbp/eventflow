"""Idempotent optional demo data; never overwrites existing events."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.models import Event


async def seed_events(session: AsyncSession) -> None:
    async with session.begin():
        for index, (title, description, capacity) in enumerate(
            [
                (
                    "EventFlow: встреча разработчиков",
                    "Обсудим API, транзакции и опыт разработки. "
                    "Демонстрационное мероприятие.",
                    30,
                ),
                (
                    "Практикум по PostgreSQL",
                    "Разбираем блокировки и конкурентный доступ на примерах. "
                    "Демонстрационное мероприятие.",
                    15,
                ),
            ],
            start=1,
        ):
            await session.execute(
                insert(Event)
                .values(
                    id=UUID(f"00000000-0000-4000-8000-{index:012d}"),
                    title=title,
                    description=description,
                    capacity=capacity,
                    starts_at=(datetime.now(UTC) + timedelta(days=7 * index)).replace(
                        second=0, microsecond=0
                    ),
                )
                .on_conflict_do_nothing(index_elements=[Event.id])
            )


async def main() -> None:
    engine = create_async_engine(str(Settings().database_url))
    try:
        async with async_sessionmaker(engine)() as session:
            await seed_events(session)
    finally:
        await engine.dispose()
    print("Demo events initialized; existing events preserved.")


if __name__ == "__main__":
    asyncio.run(main())
