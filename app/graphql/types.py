"""GraphQL Types - Definición de tipos de salida"""

import strawberry
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Enums para estados
@strawberry.enum
class EstadoFactura(Enum):
    """Estados posibles de una factura"""
    PENDIENTE = "PENDIENTE"
    ENVIADA = "ENVIADA"
    RECHAZADA = "RECHAZADA"
    ABONADA = "ABONADA"


@strawberry.enum
class EstadoLote(Enum):
    """Estados posibles de un lote"""
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    COMPLETADO = "COMPLETADO"
    ERROR = "ERROR"


# ============= ITEM TYPE =============

@strawberry.type
class ItemType:
    """Tipo para items/líneas de factura"""
    id: int
    code_reference: str
    name: str
    quantity: int
    price: float
    tax_rate: float
    discount_rate: float
    subtotal: float
    discount_amount: float
    tax_amount: float
    total: float


# ============= CUSTOMER TYPE =============

@strawberry.type
class CustomerType:
    """Tipo para cliente"""
    id: int
    names: str
    email: str
    phone: str
    identification: str
    identification_document_id: int
    legal_organization_id: int


# ============= INVOICE TYPE =============

@strawberry.type
class InvoiceType:
    """Tipo para factura"""
    id: int
    numbering_range_id: int
    reference_code: str
    observation: Optional[str]
    payment_form: str
    payment_method_code: str
    cliente_email: str
    cliente_nombre: str
    total: float
    estado: str  # Será validado en resolver
    motivo_rechazo: Optional[str]
    api_response: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    lote_id: Optional[int]
    usuario_id: Optional[int]
    
    # Campos relacionados
    items: Optional[List[ItemType]] = None
    customer: Optional[CustomerType] = None


# ============= INVOICE LIST TYPE =============

@strawberry.type
class InvoiceListType:
    """Tipo para listado paginado de facturas"""
    items: List[InvoiceType]
    total: int
    skip: int
    limit: int
    
    @property
    def pages(self) -> int:
        """Calcular total de páginas"""
        return (self.total + self.limit - 1) // self.limit
    
    @property
    def current_page(self) -> int:
        """Calcular página actual"""
        return (self.skip // self.limit) + 1


# ============= LOTE TYPE =============

@strawberry.type
class LoteType:
    """Tipo para lote"""
    id: int
    nombre_archivo: str
    fecha_carga: datetime
    total_registros: int
    registros_procesados: Optional[int]
    estado: str
    usuario_id: Optional[int]
    
    # Facturas del lote (lazy loading)
    facturas: Optional[List[InvoiceType]] = None


# ============= SIMPLE INVOICE TYPE (para resúmenes) =============

@strawberry.type
class SimpleInvoiceType:
    """Tipo simplificado de factura (para resúmenes)"""
    id: int
    reference_code: str
    cliente_email: str
    estado: str
    total: float


# ============= LOTE DETAIL TYPE =============

@strawberry.type
class LoteDetailType:
    """Tipo para detalles completos de lote"""
    id: int
    nombre_archivo: str
    fecha_carga: datetime
    total_registros: int
    registros_procesados: int
    estado: str
    facturas: Optional[List[SimpleInvoiceType]] = None


# ============= LOTE LIST TYPE =============

@strawberry.type
class LoteListType:
    """Tipo para listado paginado de lotes"""
    items: List[LoteType]
    total: int
    skip: int
    limit: int
    
    @property
    def pages(self) -> int:
        return (self.total + self.limit - 1) // self.limit


# ============= STATISTICS TYPE =============

@strawberry.type
class LoteStatisticsType:
    """Tipo para estadísticas de lote"""
    total_facturas: int
    enviadas: int
    rechazadas: int
    pendientes: int
    total_monto: float
    promedio_monto: float
    tasa_exito: float


# ============= USER TYPE =============

@strawberry.type
class UserType:
    """Tipo para usuario"""
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


# ============= AUTH RESPONSE TYPE =============

@strawberry.type
class AuthResponseType:
    """Respuesta de autenticación"""
    access_token: str
    token_type: str
    user: UserType
