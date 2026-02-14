"""GraphQL Queries - Resolvers de lectura"""

import strawberry
from typing import List, Optional
from strawberry.types import Info

from app.graphql.types import (
    InvoiceType, InvoiceListType, LoteType, LoteListType,
    LoteDetailType, LoteStatisticsType, UserType, SimpleInvoiceType
)
from app.graphql.inputs import PaginationInput
from app.services.invoice_service import InvoiceService
from app.services.lote_service import LoteService
from app.database import get_session
from app.core.deps import get_current_user
from app.models import User


@strawberry.type
class Query:
    """Queries GraphQL - Lectura de datos"""
    
    # ============= INVOICE QUERIES =============
    
    @strawberry.field
    async def invoice(
        self,
        info: Info,
        id: int
    ) -> InvoiceType:
        """
        Obtener una factura por ID.
        
        Args:
            id: ID de la factura
            
        Returns:
            InvoiceType con la factura
        """
        session = info.context.get("session")
        service = InvoiceService(session)
        invoice_response = await service.obtener_factura(id)
        
        return InvoiceType(
            id=invoice_response.id,
            numbering_range_id=invoice_response.numbering_range_id,
            reference_code=invoice_response.reference_code,
            observation=None,
            payment_form="1",
            payment_method_code="10",
            cliente_email=invoice_response.cliente_email,
            cliente_nombre=invoice_response.cliente_nombre,
            total=invoice_response.total,
            estado=invoice_response.estado,
            motivo_rechazo=invoice_response.motivo_rechazo,
            api_response=invoice_response.api_response,
            created_at=invoice_response.created_at,
            updated_at=invoice_response.updated_at,
            lote_id=invoice_response.lote_id,
            usuario_id=invoice_response.usuario_id
        )
    
    @strawberry.field
    async def invoices(
        self,
        info: Info,
        estado: Optional[str] = None,
        pagination: Optional[PaginationInput] = None
    ) -> InvoiceListType:
        """
        Listar facturas con paginación y filtros.
        
        Args:
            estado: Filtro por estado (PENDIENTE, ENVIADA, etc.)
            pagination: Parámetros de paginación (skip, limit)
            
        Returns:
            InvoiceListType con lista paginada
        """
        session = info.context.get("session")
        service = InvoiceService(session)
        
        skip = pagination.skip if pagination else 0
        limit = pagination.limit if pagination else 100
        
        list_response = await service.listar_facturas(
            estado=estado,
            skip=skip,
            limit=limit
        )
        
        items = [
            InvoiceType(
                id=inv.id,
                numbering_range_id=inv.numbering_range_id,
                reference_code=inv.reference_code,
                observation=None,
                payment_form="1",
                payment_method_code="10",
                cliente_email=inv.cliente_email,
                cliente_nombre=inv.cliente_nombre,
                total=inv.total,
                estado=inv.estado,
                motivo_rechazo=inv.motivo_rechazo,
                api_response=inv.api_response,
                created_at=inv.created_at,
                updated_at=inv.updated_at,
                lote_id=inv.lote_id,
                usuario_id=inv.usuario_id
            )
            for inv in list_response.items
        ]
        
        return InvoiceListType(
            items=items,
            total=list_response.total,
            skip=skip,
            limit=limit
        )
    
    @strawberry.field
    async def invoices_by_customer(
        self,
        info: Info,
        email: str,
        pagination: Optional[PaginationInput] = None
    ) -> InvoiceListType:
        """
        Obtener facturas de un cliente por email.
        
        Args:
            email: Email del cliente
            pagination: Parámetros de paginación
            
        Returns:
            InvoiceListType con facturas del cliente
        """
        session = info.context.get("session")
        service = InvoiceService(session)
        
        skip = pagination.skip if pagination else 0
        limit = pagination.limit if pagination else 100
        
        list_response = await service.obtener_facturas_cliente(
            email=email,
            skip=skip,
            limit=limit
        )
        
        items = [
            InvoiceType(
                id=inv.id,
                numbering_range_id=inv.numbering_range_id,
                reference_code=inv.reference_code,
                observation=None,
                payment_form="1",
                payment_method_code="10",
                cliente_email=inv.cliente_email,
                cliente_nombre=inv.cliente_nombre,
                total=inv.total,
                estado=inv.estado,
                motivo_rechazo=inv.motivo_rechazo,
                api_response=inv.api_response,
                created_at=inv.created_at,
                updated_at=inv.updated_at,
                lote_id=inv.lote_id,
                usuario_id=inv.usuario_id
            )
            for inv in list_response.items
        ]
        
        return InvoiceListType(
            items=items,
            total=list_response.total,
            skip=skip,
            limit=limit
        )
    
    # ============= LOTE QUERIES =============
    
    @strawberry.field
    async def lote(
        self,
        info: Info,
        id: int
    ) -> LoteDetailType:
        """
        Obtener un lote con detalles completos (con facturas preload).
        
        OPTIMIZACIÓN: Usa eager loading (selectinload) para prevenir N+1 problem.
        Sin optimización: 1 query para lote + 1 query por cada factura
        Con optimización: 1 query con JOIN que carga todo
        
        Args:
            id: ID del lote
            
        Returns:
            LoteDetailType con información del lote y facturas relacionadas
        """
        session = info.context.get("session")
        
        # Usar LoteRepository con método optimizado (selectinload)
        from app.repositories import LoteRepository
        lote_repo = LoteRepository(session)
        lote_detail = await lote_repo.get_with_relations(id)
        
        if not lote_detail:
            from app.api.errors.http_errors import NotFoundException
            raise NotFoundException("Lote", id)
        
        # Convertir facturas a SimpleInvoiceType
        # Ahora las facturas YA están cargadas (no genera queries adicionales)
        facturas_convertidas = [
            SimpleInvoiceType(
                id=factura.id,
                reference_code=factura.reference_code,
                cliente_email=factura.cliente_email or "",
                estado=factura.estado,
                total=factura.total
            )
            for factura in (lote_detail.facturas or [])
        ]
        
        return LoteDetailType(
            id=lote_detail.id,
            nombre_archivo=lote_detail.nombre_archivo,
            fecha_carga=lote_detail.fecha_carga,
            total_registros=lote_detail.total_registros,
            registros_procesados=lote_detail.registros_procesados,
            estado=lote_detail.estado,
            facturas=facturas_convertidas or []
        )
    
    @strawberry.field
    async def lotes(
        self,
        info: Info,
        estado: Optional[str] = None,
        pagination: Optional[PaginationInput] = None
    ) -> LoteListType:
        """
        Listar lotes con paginación y filtros (con facturas preload).
        
        OPTIMIZACIÓN: Usa eager loading (selectinload) para prevenir N+1 problem.
        Sin optimización: 1 query para listar + 1 query por cada lote para sus facturas
        Con optimización: 1 query con JOIN para todos los lotes y sus facturas
        
        Args:
            estado: Filtro por estado (PENDIENTE, PROCESANDO, COMPLETADO, etc.)
            pagination: Parámetros de paginación (skip, limit)
            
        Returns:
            LoteListType con lista de lotes y metadata
        """
        session = info.context.get("session")
        
        skip = pagination.skip if pagination else 0
        limit = pagination.limit if pagination else 100
        
        # Usar LoteRepository con método optimizado (selectinload)
        from app.repositories import LoteRepository
        lote_repo = LoteRepository(session)
        
        # Si se pide filtrar por estado, usar método especializado
        if estado:
            result = await lote_repo.get_by_estado_with_relations(
                estado=estado,
                skip=skip,
                limit=limit
            )
            total = await lote_repo.count_by_estado(estado)
        else:
            # Traer todos con relaciones
            result = await lote_repo.get_all_with_relations(
                skip=skip,
                limit=limit
            )
            total = await lote_repo.count()
        
        items = [
            LoteType(
                id=lote.id,
                nombre_archivo=lote.nombre_archivo,
                fecha_carga=lote.fecha_carga,
                total_registros=lote.total_registros,
                registros_procesados=lote.registros_procesados,
                estado=lote.estado,
                usuario_id=lote.usuario_id
            )
            for lote in result
        ]
        
        return LoteListType(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
    
    @strawberry.field
    async def lotes_historial(
        self,
        info: Info,
        pagination: Optional[PaginationInput] = None
    ) -> LoteListType:
        """
        Obtener historial de lotes (últimos primero) con facturas preload.
        
        OPTIMIZACIÓN: Usa eager loading (selectinload) para prevenir N+1 problem.
        Retorna lotes ordenados por fecha_carga DESC.
        
        Args:
            pagination: Parámetros de paginación
            
        Returns:
            LoteListType ordenado por fecha desc
        """
        session = info.context.get("session")
        
        skip = pagination.skip if pagination else 0
        limit = pagination.limit if pagination else 100
        
        # Usar LoteRepository con método optimizado (selectinload)
        from app.repositories import LoteRepository
        lote_repo = LoteRepository(session)
        
        # Obtener historial ordenado por fecha DESC
        result = await lote_repo.get_historial_with_relations(
            skip=skip,
            limit=limit
        )
        
        # Para historial, contar TODOS los lotes (sin filtro)
        total = await lote_repo.count()
        
        items = [
            LoteType(
                id=lote.id,
                nombre_archivo=lote.nombre_archivo,
                fecha_carga=lote.fecha_carga,
                total_registros=lote.total_registros,
                registros_procesados=lote.registros_procesados,
                estado=lote.estado,
                usuario_id=lote.usuario_id
            )
            for lote in result
        ]
        
        return LoteListType(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
    
    @strawberry.field
    async def lote_statistics(
        self,
        info: Info,
        lote_id: int
    ) -> LoteStatisticsType:
        """
        Obtener estadísticas de un lote (conteos y montos).
        
        OPTIMIZACIÓN: Calcula estadísticas en base de datos (no en memoria).
        Retorna agregaciones directas sin transferir datos innecesarios.
        
        Args:
            lote_id: ID del lote
            
        Returns:
            LoteStatisticsType con estadísticas del lote
        """
        session = info.context.get("session")
        
        # Usar LoteRepository para obtener estadísticas optimizadas
        from app.repositories import LoteRepository
        lote_repo = LoteRepository(session)
        
        # Obtener lote con sus facturas
        lote = await lote_repo.get_with_relations(lote_id)
        
        if not lote:
            from app.api.errors.http_errors import NotFoundException
            raise NotFoundException("Lote", lote_id)
        
        # Calcular estadísticas desde facturas cargadas
        facturas = lote.facturas or []
        
        total_facturas = len(facturas)
        enviadas = sum(1 for f in facturas if f.estado == "ENVIADA")
        rechazadas = sum(1 for f in facturas if f.estado == "RECHAZADA")
        pendientes = sum(1 for f in facturas if f.estado in ["PENDIENTE", "PROCESANDO"])
        
        total_monto = sum(f.total for f in facturas if f.total)
        promedio_monto = (total_monto / total_facturas) if total_facturas > 0 else 0.0
        tasa_exito = ((enviadas / total_facturas) * 100) if total_facturas > 0 else 0.0
        
        return LoteStatisticsType(
            total_facturas=total_facturas,
            enviadas=enviadas,
            rechazadas=rechazadas,
            pendientes=pendientes,
            total_monto=total_monto,
            promedio_monto=promedio_monto,
            tasa_exito=tasa_exito
        )
