import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def check_database(request: Request) -> None:
    try:
        async with asyncio.timeout(5):
            async with request.app.state.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError) as exc:
        raise HTTPException(503, detail="Database unavailable") from exc


@router.get("/health/ready", dependencies=[Depends(check_database)])
async def readiness() -> dict[str, str]:
    return {"status": "ok", "database": "ok"}
