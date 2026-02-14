"""Schemas de autenticación"""

from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Respuesta de login"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos decodificados del token JWT"""

    email: Optional[str] = None


class LoginResponse(BaseModel):
    """Respuesta completa de login"""

    access_token: str
    token_type: str = "bearer"
    email: str
