"""User Repository"""

from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repositorio especializado para Usuarios"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Buscar usuario por email"""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def email_exists(self, email: str) -> bool:
        """Verificar si email ya existe"""
        count = await self.count(email=email)
        return count > 0
