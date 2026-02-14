"""Base Service - Clase base para servicios de negocio"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from app.repositories.base import BaseRepository

T = TypeVar("T")
R = TypeVar("R")


class BaseService(Generic[T, R]):
    """
    Clase base abstracta para servicios de negocio.
    
    Proporciona métodos comunes reutilizables:
    - CRUD básico
    - Paginación
    - Filtrado dinámico
    - Recuento y búsqueda
    
    Tipos Genéricos:
        T: Modelo ORM (ej: Factura)
        R: Schema/DTO de respuesta (ej: InvoiceResponse)
    
    Uso:
        class InvoiceService(BaseService[Factura, InvoiceResponse]):
            def __init__(self, session: AsyncSession):
                repository = FacturaRepository(session)
                super().__init__(repository, session)
    """
    
    def __init__(self, repository: BaseRepository[T], session: AsyncSession):
        """
        Inicializar servicio con repositorio y sesión.
        
        Args:
            repository: Repositorio para acceso a datos
            session: Sesión async de base de datos
        """
        if repository is None:
            raise ValueError("Repository cannot be None")
        if session is None:
            raise ValueError("AsyncSession cannot be None")
            
        self.repository = repository
        self.session = session
    
    # ============= LECTURAS (QUERIES) =============
    
    async def get(self, id: int) -> Optional[T]:
        """
        Obtener un registro por ID.
        
        Args:
            id: ID del registro
            
        Returns:
            Modelo ORM o None si no existe
        """
        return await self.repository.get(id)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        **filters
    ) -> List[T]:
        """
        Obtener todos los registros con paginación y filtros.
        
        Args:
            skip: Registros a saltar (offset)
            limit: Límite de resultados
            **filters: Filtros dinámicos (ej: estado="ENVIADA", cliente_id=1)
            
        Returns:
            Lista de modelos ORM
        """
        return await self.repository.get_all(skip=skip, limit=limit, **filters)
    
    async def count(self, **filters) -> int:
        """
        Contar registros con filtros opcionales.
        
        Args:
            **filters: Filtros dinámicos
            
        Returns:
            Cantidad de registros
        """
        return await self.repository.count(**filters)
    
    async def exists(self, id: int) -> bool:
        """
        Verificar si un registro existe.
        
        Args:
            id: ID del registro
            
        Returns:
            True si existe, False si no
        """
        return await self.repository.exists(id)
    
    # ============= ESCRITURAS (MUTATIONS) =============
    
    async def create(self, obj: T) -> T:
        """
        Crear un nuevo registro.
        
        Nota: Servicios especializados deben sobrescribir 
        para agregar validación de negocio.
        
        Args:
            obj: Instancia del modelo a crear
            
        Returns:
            Modelo creado con ID
        """
        return await self.repository.create(obj)
    
    async def update(self, obj: T) -> T:
        """
        Actualizar un registro existente.
        
        Nota: Servicios especializados deben sobrescribir 
        para agregar validación de negocio.
        
        Args:
            obj: Instancia del modelo a actualizar
            
        Returns:
            Modelo actualizado
        """
        return await self.repository.update(obj)
    
    async def delete(self, id: int) -> bool:
        """
        Eliminar un registro por ID.
        
        Args:
            id: ID del registro a eliminar
            
        Returns:
            True si fue eliminado, False si no existía
        """
        return await self.repository.delete(id)
    
    # ============= UTILIDADES =============
    
    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> Dict[str, Any]:
        """
        Obtener resultados paginados con metadata.
        
        Muy útil para endpoints que retornan lista + paginación.
        
        Args:
            skip: Offset
            limit: Límite
            **filters: Filtros dinámicos
            
        Returns:
            {
                'items': [lista de modelos],
                'total': cantidad total,
                'skip': offset usado,
                'limit': limite usado,
                'pages': cantidad de páginas,
                'current_page': página actual
            }
        """
        items = await self.get_all(skip=skip, limit=limit, **filters)
        total = await self.count(**filters)
        
        pages = (total + limit - 1) // limit  # Redondear hacia arriba
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return {
            'items': items,
            'total': total,
            'skip': skip,
            'limit': limit,
            'pages': pages,
            'current_page': current_page
        }
    
    async def bulk_create(self, objects: List[T]) -> List[T]:
        """
        Crear múltiples registros en una transacción.
        
        Si alguno falla, se revierte toda la transacción.
        
        Args:
            objects: Lista de modelos a crear
            
        Returns:
            Lista de modelos creados
        """
        try:
            results = []
            for obj in objects:
                result = await self.repository.create(obj)
                results.append(result)
            await self.session.commit()
            return results
        except Exception as e:
            await self.session.rollback()
            raise e

