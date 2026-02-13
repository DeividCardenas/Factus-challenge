from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import User
from app.core.security import SECRET_KEY, ALGORITHM

# OAuth2PasswordBearer extrae el token del header Authorization: Bearer <token>
# "tokenUrl" es la URL que el frontend (o Swagger UI) usará para obtener el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Buscamos el usuario en la BD de forma asíncrona
    query = select(User).where(User.email == email)
    result = await session.exec(query)
    user = result.first()

    if user is None:
        raise credentials_exception
    if not user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    return user
