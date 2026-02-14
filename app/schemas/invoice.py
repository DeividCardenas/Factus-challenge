"""Schemas de factura e items"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime


# ============= ITEM SCHEMAS =============


class ItemCreate(BaseModel):
    """Item para crear factura"""

    code_reference: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0, description="Quantity must be positive")
    price: float = Field(..., ge=0, description="Price must be non-negative")
    tax_rate: float = Field(..., ge=0, le=100, description="Tax rate between 0-100")
    discount_rate: float = Field(default=0, ge=0, le=100)

    @validator("price")
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative")
        return round(v, 2)


class ItemResponse(ItemCreate):
    """Item en respuesta"""

    subtotal: float
    discount_amount: float
    tax_amount: float
    total: float


# ============= CUSTOMER SCHEMAS =============


class CustomerCreate(BaseModel):
    """Customer para crear factura"""

    names: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    identification: str = Field(..., min_length=1, max_length=50)
    identification_document_id: str = Field(..., min_length=1, max_length=10)
    legal_organization_id: str = Field(..., min_length=1, max_length=10)


# ============= INVOICE SCHEMAS =============


class InvoiceCreate(BaseModel):
    """Request para crear factura"""

    numbering_range_id: int = Field(..., gt=0)
    reference_code: str = Field(..., min_length=1, max_length=100)
    observation: Optional[str] = Field(None, max_length=500)
    payment_form: str = Field(default="1", pattern="^[1-2]$")
    payment_method_code: str = Field(default="10", min_length=1, max_length=10)
    customer: CustomerCreate
    items: List[ItemCreate] = Field(..., min_items=1)

    @validator("items")
    def validate_items(cls, items):
        if not items:
            raise ValueError("At least one item is required")
        return items

    @validator("reference_code")
    def validate_reference_unique(cls, v):
        return v.strip().upper()


class InvoiceResponse(BaseModel):
    """Respuesta de factura"""

    id: int
    reference_code: str
    cliente_email: str
    total: float
    estado: str
    motivo_rechazo: Optional[str] = None
    created_at: Optional[datetime] = None
    factus_response: Optional[dict] = None

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Respuesta paginada de facturas"""

    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class InvoiceStats(BaseModel):
    """Estadísticas de facturas"""

    total_count: int
    successful_count: int
    failed_count: int
    pending_count: int
    total_amount: float
    successful_amount: float
    success_rate: float = Field(..., ge=0, le=100)
