# Pydantic Schemas (DTOs) - Separación de Modelos de BD y API

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

# ============= SCHEMAS DE AUTH =============

class Token(BaseModel):
    """Respuesta de login"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Datos decodificados del token JWT"""
    email: Optional[str] = None

# ============= SCHEMAS DE INVOICE =============

class ItemBase(BaseModel):
    """Item base para request"""
    code_reference: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0, description="Quantity must be positive")
    price: float = Field(..., ge=0, description="Price must be non-negative")
    tax_rate: float = Field(..., ge=0, le=100, description="Tax rate between 0-100")
    discount_rate: float = Field(default=0, ge=0, le=100)
    
    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        # Limitar a 2 decimales
        return round(v, 2)

class ItemResponse(ItemBase):
    """Item en respuesta (con cálculos)"""
    subtotal: float
    discount_amount: float
    tax_amount: float
    total: float

class CustomerBase(BaseModel):
    """Cliente base"""
    names: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    identification: str = Field(..., min_length=1, max_length=50)
    identification_document_id: str = Field(..., min_length=1, max_length=10)
    legal_organization_id: str = Field(..., min_length=1, max_length=10)

class InvoiceBase(BaseModel):
    """Datos base de factura"""
    numbering_range_id: int = Field(..., gt=0)
    reference_code: str = Field(..., min_length=1, max_length=100)
    observation: Optional[str] = Field(None, max_length=500)
    payment_form: str = Field(default="1", regex="^[1-2]$")  # 1=Contado, 2=Crédito
    payment_method_code: str = Field(default="10", min_length=1, max_length=10)

class InvoiceCreate(InvoiceBase):
    """Request para crear factura"""
    customer: CustomerBase
    items: List[ItemBase] = Field(..., min_items=1)
    
    @validator('items')
    def validate_items(cls, items):
        if not items:
            raise ValueError('At least one item is required')
        return items
    
    @validator('reference_code')
    def validate_reference_unique(cls, v):
        # En un caso real, podrías hacer validación asíncrona aquí
        # o dejarlo para el service layer
        return v.strip().upper()

class InvoiceUpdate(BaseModel):
    """Request para actualizar factura (parcial)"""
    observation: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field(None, regex="^(PENDIENTE|ENVIADA|RECHAZADA|ERROR_API)$")

class InvoiceResponse(InvoiceBase):
    """Respuesta de factura"""
    id: int
    cliente_email: str
    total: float
    estado: str
    motivo_rechazo: Optional[str]
    created_at: Optional[datetime]
    factus_response: Optional[dict] = None
    
    class Config:
        from_attributes = True  # Permite crear desde ORM models

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

# ============= SCHEMAS DE LOTE =============

class LoteCreate(BaseModel):
    """Request para crear lote"""
    nombre_archivo: str = Field(..., min_length=1, max_length=255)

class LoteResponse(BaseModel):
    """Respuesta de lote"""
    id: int
    nombre_archivo: str
    fecha_carga: datetime
    total_registros: int
    total_errores: int
    estado: str
    
    class Config:
        from_attributes = True

class LoteDetailResponse(LoteResponse):
    """Respuesta detallada de lote con facturas"""
    facturas: List[InvoiceResponse]
    estadisticas: InvoiceStats

# ============= SCHEMAS DE PROCESO =============

class ProcessResult(BaseModel):
    """Resultado de procesamiento"""
    success: bool
    message: str
    task_id: Optional[str] = None
    lote_id: Optional[int] = None

class BatchUploadResponse(BaseModel):
    """Respuesta de carga masiva"""
    mensaje: str
    lote_id: int
    task_id: str
    estimated_time: Optional[int] = None  # segundos estimados

# ============= SCHEMAS DE ERROR =============

class ErrorDetail(BaseModel):
    """Detalle de un error"""
    field: str
    message: str
    type: str

class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada"""
    success: bool = False
    error: dict
    request_id: Optional[str] = None

# ============= SCHEMAS DE PAGINACIÓN =============

class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size

# ============= EJEMPLO DE USO EN ENDPOINT =============

"""
from fastapi import APIRouter, Depends, Query
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, PaginationParams

router = APIRouter()

@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    invoice_data: InvoiceCreate,  # ← Validación automática
    service: InvoiceService = Depends(get_invoice_service)
):
    # invoice_data ya está validado por Pydantic
    return await service.create_invoice(invoice_data)

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    pagination: PaginationParams = Depends(),  # ← Query params validados
    estado: Optional[str] = Query(None, regex="^(PENDIENTE|ENVIADA|RECHAZADA)$"),
    service: InvoiceService = Depends(get_invoice_service)
):
    return await service.list_invoices(
        skip=pagination.skip,
        limit=pagination.limit,
        estado=estado
    )
"""

# ============= VENTAJAS DE USAR SCHEMAS =============

"""
1. VALIDACIÓN AUTOMÁTICA
   - Tipos, rangos, formatos, regex
   - Errores descriptivos automáticos

2. DOCUMENTACIÓN AUTOMÁTICA
   - OpenAPI/Swagger generado automáticamente
   - Descripciones, ejemplos, constraints

3. SERIALIZACIÓN
   - Conversión automática de ORM models a JSON
   - Control de qué campos exponer

4. SEPARACIÓN DE CONCERNS
   - Modelos de BD != Modelos de API
   - Cambios en BD no rompen API

5. TYPE SAFETY
   - Autocompletado en IDE
   - Detección de errores en desarrollo

6. REUTILIZACIÓN
   - Schemas base compartidos
   - Herencia para crear variantes
"""
