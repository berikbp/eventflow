from fastapi import APIRouter, Depends

from app.core.security import require_organizer

router = APIRouter(prefix="/organizer", tags=["organizer"])


@router.get("/session", dependencies=[Depends(require_organizer)])
async def verify_access() -> dict[str, bool]:
    return {"authenticated": True}
