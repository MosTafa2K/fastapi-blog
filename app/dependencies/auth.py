from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.exceptions import InvalidCredentials
from app.models.user import User

oauth2_schem = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_optional_current_user(
    token: Annotated[str | None, Depends(oauth2_schem)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if token is None:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise InvalidCredentials
    query = await db.execute(select(User).where(User.id == user_id))
    user = query.scalar_one_or_none()
    if user is None:
        raise InvalidCredentials
    return user
