from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


async def require_organizer(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> None:
    token = request.app.state.settings.organizer_token
    if token is None or not token.get_secret_value():
        raise HTTPException(503, "Доступ организатора не настроен")
    if credentials is None or not compare_digest(
        credentials.credentials.encode(), token.get_secret_value().encode()
    ):
        raise HTTPException(
            401, "Неверный токен организатора", headers={"WWW-Authenticate": "Bearer"}
        )
