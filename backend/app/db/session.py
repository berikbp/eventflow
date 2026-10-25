from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseUnavailable(Exception):
    """A transient database connection failure, safe to present as HTTP 503."""


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    try:
        async with request.app.state.sessions() as session:
            yield session
    except (OSError, TimeoutError) as exc:
        raise DatabaseUnavailable from exc
    except DBAPIError as exc:
        state = getattr(exc.orig, "sqlstate", "") or ""
        if (
            isinstance(exc, (InterfaceError, OperationalError))
            or exc.connection_invalidated
            or state.startswith("08")
            or state in {"57P01", "57P02", "57P03", "53300"}
        ):
            raise DatabaseUnavailable from exc
        # Constraint/programming errors are not transient connection outages.
        raise
