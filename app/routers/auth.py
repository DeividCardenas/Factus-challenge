from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import User
from app.core.security import verify_password, create_access_token
from app.api.errors.http_errors import UnauthorizedException, ValidationException
from app.schemas import LoginResponse
from app.repositories.user_repository import UserRepository

router = APIRouter()

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """
    Login endpoint mejorado con:
    - Excepciones personalizadas
    - Repository pattern
    - Validación clara
    """
    # Validar que email no esté vacío
    if not form_data.username:
        raise ValidationException(["Email is required"])

    # Usar repository para buscar usuario
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(form_data.username)

    # Validar credenciales
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise ValidationException(["User account is inactive"])

    # Generar token
    access_token = create_access_token(subject=user.email)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        email=user.email
    )
