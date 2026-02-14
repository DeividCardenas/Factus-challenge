from typing import Optional
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import User
from app.core.security import SECRET_KEY, ALGORITHM
from app.api.errors.http_errors import UnauthorizedException
from app.repositories.user_repository import UserRepository

# OAuth2PasswordBearer extrae el token del header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Obtener usuario actual desde el token JWT.
    Mejorado con exception personalizada y repository pattern.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise UnauthorizedException("Invalid token: no email")
    except JWTError:
        raise UnauthorizedException("Invalid token")

    # Usar repository para obtener usuario
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(email)

    if user is None:
        raise UnauthorizedException("User not found")
    
    if not user.is_active:
        raise UnauthorizedException("User account is inactive")

    return user
