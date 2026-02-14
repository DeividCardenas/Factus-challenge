"""Lote Repository - Repositorio especializado para Lotes con eager loading"""

from typing import List, Optional, Dict, Any
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Lote
from app.repositories.base import BaseRepository


class LoteRepository(BaseRepository[Lote]):
    """
    Repositorio especializado para Lotes.
    
    Implementa:
    - Eager loading para evitar N+1
    - Métodos específicos del dominio
    - Query optimization con selectinload
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Lote, session)

    # ============= EAGER LOADING METHODS =============
    
    async def get_with_relations(self, id: int) -> Optional[Lote]:
        """
        Obtener lote con todas sus relaciones (eager loading).
        
        Optimización: Usa selectinload para evitar N+1 queries.
        Cuando accedas a lote.facturas, ya estarán cargadas.
        
        Args:
            id: ID del lote
            
        Returns:
            Lote con relaciones cargadas anticipadamente
        """
        query = (
            select(Lote)
            .where(Lote.id == id)
            .options(selectinload(Lote.facturas))
        )
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Lote]:
        """
        Obtener todos los lotes con relaciones (eager loading).
        
        Optimización: Evita N+1 queries cuando GraphQL accede a facturas.
        
        Args:
            skip: Offset para paginación
            limit: Límite de resultados
            **filters: Filtros dinámicos (ej: estado="PENDIENTE")
            
        Returns:
            Lista de lotes con facturas precargadas
        """
        query = select(Lote).options(selectinload(Lote.facturas))
        
        # Aplicar filtros
        for key, value in filters.items():
            if hasattr(Lote, key) and value is not None:
                query = query.where(getattr(Lote, key) == value)
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    # ============= DOMAIN-SPECIFIC METHODS =============
    
    async def get_by_nombre(self, nombre: str) -> Optional[Lote]:
        """Buscar lote por nombre de archivo (sin relaciones)"""
        query = select(Lote).where(Lote.nombre_archivo == nombre)
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_by_nombre_with_relations(self, nombre: str) -> Optional[Lote]:
        """Buscar lote por nombre con eager loading de facturas"""
        query = (
            select(Lote)
            .where(Lote.nombre_archivo == nombre)
            .options(selectinload(Lote.facturas))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_pendientes(self) -> List[Lote]:
        """Obtener lotes pendientes de procesamiento (sin relaciones)"""
        query = select(Lote).where(Lote.estado == "PENDIENTE")
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pendientes_with_relations(self) -> List[Lote]:
        """Obtener lotes pendientes CON facturas (eager loading)"""
        query = (
            select(Lote)
            .where(Lote.estado == "PENDIENTE")
            .options(selectinload(Lote.facturas))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_procesando(self) -> List[Lote]:
        """Obtener lotes en proceso (sin relaciones)"""
        query = select(Lote).where(Lote.estado == "PROCESANDO")
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_procesando_with_relations(self) -> List[Lote]:
        """Obtener lotes en proceso CON facturas (eager loading)"""
        query = (
            select(Lote)
            .where(Lote.estado == "PROCESANDO")
            .options(selectinload(Lote.facturas))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_completados_with_relations(self) -> List[Lote]:
        """Obtener lotes completados CON facturas (eager loading)"""
        query = (
            select(Lote)
            .where(Lote.estado == "COMPLETADO")
            .options(selectinload(Lote.facturas))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    # ============= ADVANCED QUERIES =============
    
    async def get_historial_with_relations(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Lote]:
        """
        Obtener historial de lotes ordenado por fecha descendente.
        Con eager loading para evitar N+1.
        
        Args:
            skip: Paginación offset
            limit: Paginación limit
            
        Returns:
            Lotes ordenados por fecha (DESC) con facturas precargadas
        """
        query = (
            select(Lote)
            .options(selectinload(Lote.facturas))
            .order_by(Lote.fecha_carga.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_estado_with_relations(
        self,
        estado: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Lote]:
        """
        Obtener lotes filtrados por estado con relaciones.
        
        Args:
            estado: Estado del lote
            skip: Paginación
            limit: Límite
            
        Returns:
            Lotes con facturas precargadas
        """
        query = (
            select(Lote)
            .where(Lote.estado == estado)
            .options(selectinload(Lote.facturas))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_by_estado(self, estado: str) -> int:
        """Contar lotes por estado"""
        query = select(Lote).where(Lote.estado == estado)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def get_estadisticas_totales(self) -> Dict[str, Any]:
        """
        Obtener estadísticas globales de lotes.
        
        Returns:
            {
                'total': int,
                'pendientes': int,
                'procesando': int,
                'completados': int,
                'errores': int
            }
        """
        all_lotes = await self.get_all()
        
        total = len(all_lotes)
        pendientes = len([l for l in all_lotes if l.estado == "PENDIENTE"])
        procesando = len([l for l in all_lotes if l.estado == "PROCESANDO"])
        completados = len([l for l in all_lotes if l.estado == "COMPLETADO"])
        errores = len([l for l in all_lotes if l.estado == "ERROR"])
        
        return {
            "total": total,
            "pendientes": pendientes,
            "procesando": procesando,
            "completados": completados,
            "errores": errores
        }
