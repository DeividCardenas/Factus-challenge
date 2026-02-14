# Base Repository Pattern - Mejora Crítica #1

from typing import Generic, TypeVar, Type, Optional, List
from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)

class BaseRepository(Generic[ModelType]):
    """
    Repositorio base genérico con operaciones CRUD.
    Elimina código repetitivo y centraliza lógica de acceso a datos.
    
    Uso:
        class UserRepository(BaseRepository[User]):
            # Métodos específicos si necesitas
            pass
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get(self, id: int) -> Optional[ModelType]:
        """Obtener por ID"""
        return await self.session.get(self.model, id)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Obtener todos con paginación y filtros"""
        query = select(self.model).offset(skip).limit(limit)
        
        # Aplicar filtros dinámicos
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, obj: ModelType) -> ModelType:
        """Crear nuevo registro"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def update(self, obj: ModelType) -> ModelType:
        """Actualizar registro existente"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def delete(self, id: int) -> bool:
        """Eliminar por ID"""
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False
    
    async def count(self, **filters) -> int:
        """Contar registros con filtros"""
        from sqlalchemy import func
        
        query = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def exists(self, id: int) -> bool:
        """Verificar si existe"""
        obj = await self.get(id)
        return obj is not None
