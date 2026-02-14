"""Schemas de lotes"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.invoice import InvoiceResponse, InvoiceStats


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

    facturas: List[InvoiceResponse] = []
    estadisticas: Optional[InvoiceStats] = None


# ============= PROCESS SCHEMAS =============


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
    estimated_time: Optional[int] = None
