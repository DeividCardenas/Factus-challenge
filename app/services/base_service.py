"""Base Service - Clase abstracta para servicios de negocio"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from app.repositories.base import BaseRepository

T = TypeVar("T")
R = TypeVar("R")


class BaseService(Generic[T, R]):
    """
    Clase base para servicios de negocio.
    
    T: Modelo ORM (ej: Factura)
    R: Schema/DTO de respuesta (ej: InvoiceResponse)
    """
    
    def __init__(self, repository: BaseRepository[T], session: AsyncSession):
        """
        Inicializar servicio con repositorio y sesión.
        
        Args:
            repository: Repositorio para acceso a datos
            session: Sesión async de base de datos
        """
        self.repository = repository
        self.session = session
    
    async def get(self, id: int) -> Optional[T]:
        """Obtener por ID"""
        return await self.repository.get(id)
    
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Obtener todos con paginación y filtros"""
        return await self.repository.get_all(skip=skip, limit=limit, **filters)
    
    async def count(self, **filters) -> int:
        """Contar registros"""
        return await self.repository.count(**filters)
    
    async def exists(self, id: int) -> bool:
        """Verificar existencia"""
        return await self.repository.exists(id)
