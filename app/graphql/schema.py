"""GraphQL Schema - Unificación de tipos, queries, mutations"""

import strawberry
from typing import Optional
from strawberry.types import Info

# Importar todos los tipos
from app.graphql.types import (
    InvoiceType, InvoiceListType, LoteType, LoteListType,
    LoteDetailType, LoteStatisticsType, UserType, AuthResponseType
)

# Importar inputs
from app.graphql.inputs import (
    InvoiceCreateInput, PaginationInput, LoteCreateInput, LoginInput
)

# Importar Service Layer
from app.services.invoice_service import InvoiceService
from app.services.lote_service import LoteService
from app.services.auth_service import AuthService

# Importar Query existente
from app.graphql.queries import Query


# ============= MUTATIONS =============

@strawberry.type
class Mutation:
    """Mutations GraphQL - Creación y modificación de datos"""
    
    @strawberry.mutation
    async def create_invoice(
        self,
        info: Info,
        invoice_input: InvoiceCreateInput
    ) -> InvoiceType:
        """
        Crear una nueva factura via GraphQL.
        
        Args:
            invoice_input: Datos de la factura
            
        Returns:
            InvoiceType creado
        """
        session = info.context.get("session")
        # Nota: En producción, deberías obtener current_user del contexto
        current_user = info.context.get("user")
        usuario_id = current_user.id if current_user else 1
        
        service = InvoiceService(session)
        # Convertir input de GraphQL a schema Pydantic
        from app.schemas.invoice import (
            InvoiceCreate, ItemCreate, CustomerCreate
        )
        
        items = [
            ItemCreate(
                code_reference=item.code_reference,
                name=item.name,
                quantity=item.quantity,
                price=item.price,
                tax_rate=item.tax_rate,
                discount_rate=item.discount_rate
            )
            for item in invoice_input.items
        ]
        
        customer = CustomerCreate(
            names=invoice_input.customer.names,
            email=invoice_input.customer.email,
            phone=invoice_input.customer.phone,
            identification=invoice_input.customer.identification,
            identification_document_id=invoice_input.customer.identification_document_id,
            legal_organization_id=invoice_input.customer.legal_organization_id
        )
        
        factura_create = InvoiceCreate(
            numbering_range_id=invoice_input.numbering_range_id,
            reference_code=invoice_input.reference_code,
            observation=invoice_input.observation,
            payment_form=invoice_input.payment_form,
            payment_method_code=invoice_input.payment_method_code,
            customer=customer,
            items=items
        )
        
        result = await service.crear_factura(factura_create, usuario_id)
        
        return InvoiceType(
            id=result.id,
            numbering_range_id=result.numbering_range_id,
            reference_code=result.reference_code,
            observation=result.observation,
            payment_form=result.payment_form,
            payment_method_code=result.payment_method_code,
            cliente_email=result.cliente_email,
            cliente_nombre=result.cliente_nombre,
            total=result.total,
            estado=result.estado,
            motivo_rechazo=result.motivo_rechazo,
            api_response=result.api_response,
            created_at=result.created_at,
            updated_at=result.updated_at,
            lote_id=result.lote_id,
            usuario_id=result.usuario_id
        )
    
    @strawberry.mutation
    async def update_invoice_status(
        self,
        info: Info,
        invoice_id: int,
        nuevo_estado: str,
        motivo: Optional[str] = None
    ) -> InvoiceType:
        """
        Actualizar estado de una factura.
        
        Args:
            invoice_id: ID de la factura
            nuevo_estado: Nuevo estado
            motivo: Motivo (si es rechazo)
            
        Returns:
            InvoiceType actualizado
        """
        session = info.context.get("session")
        service = InvoiceService(session)
        
        result = await service.actualizar_estado_factura(
            invoice_id,
            nuevo_estado,
            motivo
        )
        
        return InvoiceType(
            id=result.id,
            numbering_range_id=result.numbering_range_id,
            reference_code=result.reference_code,
            observation=result.observation,
            payment_form=result.payment_form,
            payment_method_code=result.payment_method_code,
            cliente_email=result.cliente_email,
            cliente_nombre=result.cliente_nombre,
            total=result.total,
            estado=result.estado,
            motivo_rechazo=result.motivo_rechazo,
            api_response=result.api_response,
            created_at=result.created_at,
            updated_at=result.updated_at,
            lote_id=result.lote_id,
            usuario_id=result.usuario_id
        )
    
    @strawberry.mutation
    async def create_lote(
        self,
        info: Info,
        lote_input: LoteCreateInput
    ) -> LoteType:
        """
        Crear un nuevo lote.
        
        Args:
            lote_input: Datos del lote
            
        Returns:
            LoteType creado
        """
        session = info.context.get("session")
        current_user = info.context.get("user")
        usuario_id = current_user.id if current_user else 1
        
        from app.schemas.lote import LoteCreate
        
        service = LoteService(session)
        result = await service.crear_lote(
            LoteCreate(
                nombre_archivo=lote_input.nombre_archivo,
                total_registros=lote_input.total_registros
            ),
            usuario_id
        )
        
        return LoteType(
            id=result.id,
            nombre_archivo=result.nombre_archivo,
            fecha_carga=result.fecha_carga,
            total_registros=result.total_registros,
            registros_procesados=result.registros_procesados,
            estado=result.estado,
            usuario_id=result.usuario_id
        )


# ============= SCHEMA =============

# Importar extensiones GraphQL
from app.graphql.extensions import CustomErrorHandling, PerformanceMonitoring

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        CustomErrorHandling,
        PerformanceMonitoring,
    ]
)

