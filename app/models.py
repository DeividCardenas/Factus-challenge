from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

# --- MODELO LOTE (Cabecera) ---
class Lote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_archivo: str
    fecha_carga: datetime = Field(default_factory=datetime.utcnow)
    total_registros: int = 0
    estado: str = Field(default="PROCESANDO") # PROCESANDO, COMPLETADO, ERROR

    # Relación
    facturas: List["Factura"] = Relationship(back_populates="lote")


# --- MODELO FACTURA (Detalle) ---
class Factura(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="lote.id")

    reference_code: str = Field(index=True)
    cliente_email: str
    total: float = 0.0

    estado: str # RECHAZADA, ENVIADA, ERROR_API
    motivo_rechazo: Optional[str] = None

    # JSONB para guardar respuesta cruda de API
    api_response: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Relación
    lote: Optional[Lote] = Relationship(back_populates="facturas")
