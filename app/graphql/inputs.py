"""GraphQL Inputs - Definición de inputs (entradas)"""

import strawberry
from typing import List, Optional


# ============= ITEM INPUT =============

@strawberry.input
class ItemInput:
    """Input para crear/actualizar items"""
    code_reference: str
    name: str
    quantity: int
    price: float
    tax_rate: float = 0.0
    discount_rate: float = 0.0


# ============= CUSTOMER INPUT =============

@strawberry.input
class CustomerInput:
    """Input para cliente"""
    names: str
    email: str
    phone: str
    identification: str
    identification_document_id: int
    legal_organization_id: int


# ============= INVOICE INPUT =============

@strawberry.input
class InvoiceCreateInput:
    """Input para crear factura"""
    numbering_range_id: int
    reference_code: str
    observation: Optional[str] = None
    payment_form: str = "1"
    payment_method_code: str = "10"
    customer: CustomerInput
    items: List[ItemInput]


@strawberry.input
class InvoiceUpdateInput:
    """Input para actualizar factura"""
    observation: Optional[str] = None
    payment_form: Optional[str] = None
    payment_method_code: Optional[str] = None


# ============= LOTE INPUT =============

@strawberry.input
class LoteCreateInput:
    """Input para crear lote"""
    nombre_archivo: str
    total_registros: int


@strawberry.input
class LoteUpdateInput:
    """Input para actualizar lote"""
    estado: str


# ============= PAGINATION INPUT =============

@strawberry.input
class PaginationInput:
    """Input para paginación"""
    skip: int = 0
    limit: int = 100


# ============= LOGIN INPUT =============

@strawberry.input
class LoginInput:
    """Input para login"""
    email: str
    password: str
