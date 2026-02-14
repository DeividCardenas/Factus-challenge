"""Invoice Service - Lógica de negocio para facturas"""

from typing import Optional, List, Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Factura, Lote
from app.repositories.factura_repository import FacturaRepository
from app.services.base_service import BaseService
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceListResponse
from app.api.errors.http_errors import (
    NotFoundException, 
    ValidationException,
    ConflictException
)


class InvoiceService(BaseService[Factura, InvoiceResponse]):
    """
    Servicio de negocio para gestión de facturas.
    
    Usada por:
    - REST endpoints (/facturas)
    - GraphQL resolvers (query_invoices)
    - Background tasks (Celery)
    """
    
    def __init__(self, session: AsyncSession):
        """Inicializar con FacturaRepository"""
        repository = FacturaRepository(session)
        super().__init__(repository, session)
        self.repo = repository
    
    # ============= QUERIES =============
    
    async def obtener_factura(self, factura_id: int) -> InvoiceResponse:
        """
        Obtener factura por ID.
        
        Raises:
            NotFoundException: Si no existe la factura
        """
        factura = await self.repo.get(factura_id)
        if not factura:
            raise NotFoundException("Factura", factura_id)
        return InvoiceResponse.from_orm(factura)
    
    async def obtener_facturas_cliente(
        self,
        email: str,
        skip: int = 0,
        limit: int = 100
    ) -> InvoiceListResponse:
        """
        Obtener facturas de un cliente por email.
        
        Returns:
            InvoiceListResponse con paginación
        """
        facturas = await self.repo.get_by_cliente_email(email, skip, limit)
        total = await self.repo.count(cliente_email=email)
        
        items = [InvoiceResponse.from_orm(f) for f in facturas]
        return InvoiceListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def obtener_facturas_lote(
        self,
        lote_id: int,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> InvoiceListResponse:
        """
        Obtener facturas de un lote.
        
        Args:
            lote_id: ID del lote
            estado: Filtro opcional por estado
            skip: Paginación
            limit: Límite de resultados
            
        Returns:
            InvoiceListResponse con facturas del lote
        """
        facturas = await self.repo.get_by_lote(lote_id, estado, skip, limit)
        total = await self.repo.count(lote_id=lote_id, **{"estado": estado} if estado else {})
        
        items = [InvoiceResponse.from_orm(f) for f in facturas]
        return InvoiceListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def obtener_estadisticas_lote(self, lote_id: int) -> Dict[str, Any]:
        """
        Obtener estadísticas de un lote.
        
        Returns:
            {
                'total': int,
                'enviadas': int,
                'rechazadas': int,
                'pendientes': int,
                'total_monto': float,
                'promedio_monto': float
            }
        """
        stats = await self.repo.get_estadisticas_lote(lote_id)
        if not stats:
            raise NotFoundException("Lote", lote_id)
        return stats
    
    async def listar_facturas(
        self,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> InvoiceListResponse:
        """
        Listar todas las facturas con filtros opcionales.
        
        Args:
            estado: Filtro por estado (opcional)
            skip: Paginación
            limit: Límite
            
        Returns:
            InvoiceListResponse con facturas
        """
        filters = {"estado": estado} if estado else {}
        facturas = await self.repo.get_all(skip=skip, limit=limit, **filters)
        total = await self.repo.count(**filters)
        
        items = [InvoiceResponse.from_orm(f) for f in facturas]
        return InvoiceListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
    
    # ============= MUTATIONS =============
    
    async def crear_factura(
        self,
        factura_in: InvoiceCreate,
        usuario_id: int
    ) -> InvoiceResponse:
        """
        Crear una nueva factura.
        
        Args:
            factura_in: Datos de entrada validados
            usuario_id: ID del usuario que crea
            
        Returns:
            InvoiceResponse con la factura creada
            
        Raises:
            ConflictException: Si ya existe factura con mismo código
            ValidationException: Si hay validación fallida
        """
        # Validar que no exista ya
        existing = await self.repo.get_by_reference_code(factura_in.reference_code)
        if existing:
            raise ConflictException(
                f"Factura con referencia '{factura_in.reference_code}' ya existe"
            )
        
        # Crear modelo ORM
        factura = Factura(
            numbering_range_id=factura_in.numbering_range_id,
            reference_code=factura_in.reference_code,
            cliente_email=factura_in.customer.email,
            cliente_nombre=factura_in.customer.name,
            total=sum(item.price * item.quantity for item in factura_in.items),
            estado="PENDIENTE",
            usuario_id=usuario_id
        )
        
        # Guardar
        created = await self.repo.create(factura)
        return InvoiceResponse.from_orm(created)
    
    async def actualizar_estado_factura(
        self,
        factura_id: int,
        nuevo_estado: str,
        motivo: Optional[str] = None
    ) -> InvoiceResponse:
        """
        Actualizar estado de una factura.
        
        Args:
            factura_id: ID de la factura
            nuevo_estado: Nuevo estado (PENDIENTE, ENVIADA, RECHAZADA, ABONADA)
            motivo: Motivo si es rechazo
            
        Returns:
            InvoiceResponse actualizada
            
        Raises:
            NotFoundException: Si no existe la factura
        """
        # Validar que exista
        factura = await self.repo.get(factura_id)
        if not factura:
            raise NotFoundException("Factura", factura_id)
        
        # Actualizar
        await self.repo.update_estado(
            factura_id,
            nuevo_estado,
            motivo_rechazo=motivo
        )
        
        # Retornar actualizada
        updated = await self.repo.get(factura_id)
        return InvoiceResponse.from_orm(updated)
    
    async def bulk_crear_facturas(
        self,
        facturas_in: List[InvoiceCreate],
        usuario_id: int
    ) -> Dict[str, Any]:
        """
        Crear múltiples facturas en lote.
        
        Args:
            facturas_in: Lista de facturas
            usuario_id: ID del usuario
            
        Returns:
            {
                'created': int,
                'failed': int,
                'facturas': List[InvoiceResponse]
            }
        """
        created_facturas = []
        failed = 0
        
        for factura_in in facturas_in:
            try:
                created = await self.crear_factura(factura_in, usuario_id)
                created_facturas.append(created)
            except Exception as e:
                failed += 1
                # Log del error pero continuar
                continue
        
        return {
            "created": len(created_facturas),
            "failed": failed,
            "facturas": created_facturas
        }
