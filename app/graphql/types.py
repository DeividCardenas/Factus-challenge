import strawberry
from typing import List, Optional
from datetime import datetime
from strawberry.scalars import JSON

@strawberry.type
class FacturaType:
    id: int
    reference_code: str
    cliente_email: str
    total: float
    estado: str
    motivo_rechazo: Optional[str]
    api_response: Optional[JSON]

@strawberry.type
class LoteType:
    id: int
    nombre_archivo: str
    fecha_carga: datetime
    total_registros: int
    total_errores: int
    estado: str
    facturas: List[FacturaType]
