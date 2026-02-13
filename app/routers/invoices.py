import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.core.deps import get_current_user
from app.models import User, Factura
from app.services.api_client import factus_client

router = APIRouter()

# --- Esquemas Pydantic para Input ---
# Estos esquemas definen qué JSON esperamos recibir en el Body del POST

class TaxCreate(BaseModel):
    code: str = "1"
    name: str = "IVA"
    rate: float
    amount: float

class ItemCreate(BaseModel):
    code_reference: str
    name: str
    quantity: int
    price: float
    tax_rate: float
    discount_rate: float = 0
    # taxes: Optional[TaxCreate] # Simplificación: calculamos impuestos en backend o recibimos simple

class CustomerCreate(BaseModel):
    names: str
    email: str
    identification: str
    identification_document_id: str
    legal_organization_id: str

class FacturaCreate(BaseModel):
    numbering_range_id: int
    reference_code: str
    observation: Optional[str] = None
    payment_form: str = "1"
    payment_method_code: str = "10"
    customer: CustomerCreate
    items: List[ItemCreate]


@router.post("/facturas", response_model=dict)
async def crear_factura_individual(
    factura_in: FacturaCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Crea una factura individual, la envía a la DIAN (simulado) y la guarda.
    Requiere autenticación.
    """

    # 1. Validación y Cálculo de Totales
    total_bruto = 0.0
    total_impuestos = 0.0

    items_transformados = []

    for item in factura_in.items:
        # Validaciones básicas
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida en item {item.code_reference}")
        if item.price < 0:
             raise HTTPException(status_code=400, detail=f"Precio inválido en item {item.code_reference}")

        # Cálculos
        subtotal_linea = item.price * item.quantity
        impuesto_linea = subtotal_linea * (item.tax_rate / 100)

        total_bruto += subtotal_linea
        total_impuestos += impuesto_linea

        # Estructura para API Factus (mirando transformer.py)
        item_struct = {
            "code_reference": item.code_reference,
            "name": item.name,
            "quantity": item.quantity,
            "price": item.price,
            "tax_rate": item.tax_rate,
            "discount_rate": item.discount_rate,
            "taxes": [
                {
                    "code": "1",
                    "name": "IVA",
                    "rate": item.tax_rate,
                    "amount": impuesto_linea
                }
            ]
        }
        items_transformados.append(item_struct)

    # 2. Construir Payload para API Factus
    factura_payload = {
        "numbering_range_id": factura_in.numbering_range_id,
        "reference_code": factura_in.reference_code,
        "observation": factura_in.observation,
        "payment_form": factura_in.payment_form,
        "payment_method_code": factura_in.payment_method_code,
        "customer": factura_in.customer.dict(),
        "items": items_transformados
    }

    # 3. Enviar a Factus API (Async)
    # Reutilizamos factus_client
    resultado_api = await factus_client.enviar_factura(factura_payload)

    es_exito = resultado_api.get("status") in [200, 201]
    estado_final = "ENVIADA" if es_exito else "ERROR_API"
    motivo = None
    if not es_exito:
        motivo = f"API Error: {resultado_api.get('status')} - {resultado_api.get('error', '')}"

    # 4. Guardar en Base de Datos
    # Lote ID es NULL porque es individual
    nueva_factura = Factura(
        reference_code=factura_in.reference_code,
        cliente_email=factura_in.customer.email,
        total=total_bruto,
        estado=estado_final,
        motivo_rechazo=motivo,
        api_response=resultado_api,
        lote_id=None
    )

    session.add(nueva_factura)
    await session.commit()
    await session.refresh(nueva_factura)

    return {
        "factura_id": nueva_factura.id,
        "estado": estado_final,
        "dian_response": resultado_api
    }
