import strawberry
from typing import List, Optional

@strawberry.type
class EstadoConexion:
    codigo: int
    mensaje: str
    data: Optional[str]

@strawberry.type
class ItemFactura:
    description: str
    price: float
    quantity: int
    tax_rate: float
    tax_amount: float
    # Agrega aquí los nuevos campos si ya actualizaste (code_reference, etc)

@strawberry.type
class ClienteFactura:
    names: str
    email: str

@strawberry.type
class FacturaTransformada:
    reference_code: str
    customer: ClienteFactura
    items: List[ItemFactura]
    total_bruto: float
    total_impuestos: float