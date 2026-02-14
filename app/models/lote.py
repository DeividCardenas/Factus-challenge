from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from .factura import Factura

class Lote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_archivo: str = Field(index=True)
    fecha_carga: datetime = Field(default_factory=datetime.utcnow)
    total_registros: int = 0
    total_errores: int = 0
    estado: str = "PROCESADO"

    facturas: List["Factura"] = Relationship(back_populates="lote")
