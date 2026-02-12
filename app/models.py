from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB # <--- Importante para Postgres

class Lote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_archivo: str = Field(index=True)
    fecha_carga: datetime = Field(default_factory=datetime.utcnow)
    total_registros: int = 0
    total_errores: int = 0
    estado: str = "PROCESADO" 
    
    facturas: List["Factura"] = Relationship(back_populates="lote")

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
    lote: Optional[Lote] = Relationship(back_populates="facturas")
