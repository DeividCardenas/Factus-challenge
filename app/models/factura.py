from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .lote import Lote

class Factura(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Índices para búsquedas rápidas (B-Tree en Postgres)
    reference_code: str = Field(index=True)
    cliente_email: str = Field(index=True)
    
    total: float
    estado: str = Field(index=True) # PENDIENTE, ENVIADA, RECHAZADA
    motivo_rechazo: Optional[str] = None
    
    # Columna JSONB Nativa (Alta velocidad de lectura/escritura de JSON)
    # SQLModel usa 'sa_column' para pasar configuraciones avanzadas a SQLAlchemy
    api_response: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    
    lote_id: Optional[int] = Field(default=None, foreign_key="lote.id")
    lote: Optional["Lote"] = Relationship(back_populates="facturas")
