"""Lote Service - Lógica de negocio para lotes"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Lote, Factura
from app.repositories import LoteRepository
from app.repositories.factura_repository import FacturaRepository
from app.services.base_service import BaseService
from app.schemas.lote import LoteCreate, LoteResponse, LoteDetailResponse
from app.api.errors.http_errors import NotFoundException, ValidationException


class LoteService(BaseService[Lote, LoteResponse]):
    """
    Servicio de negocio para gestión de lotes (batches).
    
    Usada por:
    - Document upload endpoint (/emitir-facturas-masivas)
    - GraphQL resolvers (query_lotes)
    - Background tasks (Celery - process_documents)
    """
    
    def __init__(self, session: AsyncSession):
        """Inicializar con LoteRepository"""
        repository = LoteRepository(session)
        super().__init__(repository, session)
        self.lote_repo = repository
        self.factura_repo = FacturaRepository(session)
    
    # ============= QUERIES =============
    
    async def obtener_lote(self, lote_id: int) -> LoteDetailResponse:
        """
        Obtener lote con detalles completos.
        
        Args:
            lote_id: ID del lote
            
        Returns:
            LoteDetailResponse con facturas incluidas
            
        Raises:
            NotFoundException: Si no existe el lote
        """
        lote = await self.lote_repo.get(lote_id)
        if not lote:
            raise NotFoundException("Lote", lote_id)
        
        # Obtener facturas del lote
        facturas = await self.factura_repo.get_by_lote(lote_id)
        
        return LoteDetailResponse(
            id=lote.id,
            nombre_archivo=lote.nombre_archivo,
            fecha_carga=lote.fecha_carga,
            total_registros=lote.total_registros,
            registros_procesados=len(facturas),
            estado=lote.estado,
            facturas=[
                {"id": f.id, "reference_code": f.reference_code, "estado": f.estado}
                for f in facturas
            ]
        )
    
    async def obtener_lotes_pendientes(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[LoteResponse]:
        """
        Obtener lotes pendientes de procesamiento.
        
        Returns:
            Lista de lotes en estado PENDIENTE
        """
        lotes = await self.lote_repo.get_pendientes()
        return [
            LoteResponse.from_orm(lote)
            for lote in lotes[skip:skip+limit]
        ]
    
    async def obtener_lotes_procesando(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[LoteResponse]:
        """
        Obtener lotes en proceso.
        
        Returns:
            Lista de lotes en estado PROCESANDO
        """
        lotes = await self.lote_repo.get_procesando()
        return [
            LoteResponse.from_orm(lote)
            for lote in lotes[skip:skip+limit]
        ]
    
    async def listar_lotes(
        self,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Listar todos los lotes con filtros.
        
        Args:
            estado: Filtro por estado (PENDIENTE, PROCESANDO, COMPLETADO)
            skip: Paginación
            limit: Límite
            
        Returns:
            {
                'items': List[LoteResponse],
                'total': int,
                'skip': int,
                'limit': int
            }
        """
        filters = {"estado": estado} if estado else {}
        lotes = await self.lote_repo.get_all(skip=skip, limit=limit, **filters)
        total = await self.lote_repo.count(**filters)
        
        return {
            "items": [LoteResponse.from_orm(lote) for lote in lotes],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def obtener_historial_lotes(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Obtener historial de lotes (últimos primero).
        
        Returns:
            Lotes ordenados por fecha de carga descendente
        """
        lotes = await self.lote_repo.get_all(skip=skip, limit=limit)
        total = await self.lote_repo.count()
        
        # Ordenar por fecha descendente
        lotes_sorted = sorted(
            lotes,
            key=lambda x: x.fecha_carga or datetime.min,
            reverse=True
        )
        
        return {
            "items": [LoteResponse.from_orm(lote) for lote in lotes_sorted],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    # ============= MUTATIONS =============
    
    async def crear_lote(
        self,
        lote_in: LoteCreate,
        usuario_id: int
    ) -> LoteResponse:
        """
        Crear nuevo lote.
        
        Args:
            lote_in: Datos del lote
            usuario_id: ID del usuario que crea
            
        Returns:
            LoteResponse con lote creado
        """
        lote = Lote(
            nombre_archivo=lote_in.nombre_archivo,
            total_registros=lote_in.total_registros or 0,
            estado="PENDIENTE",
            usuario_id=usuario_id,
            fecha_carga=datetime.utcnow()
        )
        
        created = await self.lote_repo.create(lote)
        return LoteResponse.from_orm(created)
    
    async def actualizar_estado_lote(
        self,
        lote_id: int,
        nuevo_estado: str,
        registros_procesados: Optional[int] = None
    ) -> LoteResponse:
        """
        Actualizar estado de un lote.
        
        Args:
            lote_id: ID del lote
            nuevo_estado: Nuevo estado
            registros_procesados: Cantidad de registros procesados
            
        Returns:
            LoteResponse actualizado
            
        Raises:
            NotFoundException: Si no existe el lote
        """
        lote = await self.lote_repo.get(lote_id)
        if not lote:
            raise NotFoundException("Lote", lote_id)
        
        # Actualizar
        lote.estado = nuevo_estado
        if registros_procesados is not None:
            lote.registros_procesados = registros_procesados
        
        updated = await self.lote_repo.update(lote)
        return LoteResponse.from_orm(updated)
    
    async def obtener_estadisticas_lote(
        self,
        lote_id: int
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas completas de un lote.
        
        Args:
            lote_id: ID del lote
            
        Returns:
            {
                'total_facturas': int,
                'enviadas': int,
                'rechazadas': int,
                'pendientes': int,
                'total_monto': float,
                'promedio_monto': float,
                'tasa_exito': float (%)
            }
        """
        lote = await self.lote_repo.get(lote_id)
        if not lote:
            raise NotFoundException("Lote", lote_id)
        
        stats = await self.factura_repo.get_estadisticas_lote(lote_id)
        
        if not stats:
            return {
                "total_facturas": 0,
                "enviadas": 0,
                "rechazadas": 0,
                "pendientes": 0,
                "total_monto": 0.0,
                "promedio_monto": 0.0,
                "tasa_exito": 0.0
            }
        
        total = stats.get("total", 0)
        tasa_exito = (stats.get("enviadas", 0) / total * 100) if total > 0 else 0.0
        
        return {
            "total_facturas": total,
            "enviadas": stats.get("enviadas", 0),
            "rechazadas": stats.get("rechazadas", 0),
            "pendientes": stats.get("pendientes", 0),
            "total_monto": stats.get("total_monto", 0.0),
            "promedio_monto": stats.get("promedio_monto", 0.0),
            "tasa_exito": round(tasa_exito, 2)
        }
