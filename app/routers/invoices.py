import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.core.deps import get_current_user
from app.models import User, Factura
from app.services.api_client import factus_client
from app.repositories.factura_repository import FacturaRepository
from app.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceListResponse,
)
from app.api.errors.http_errors import ValidationException, NotFoundException, ConflictException

router = APIRouter()


@router.post("/facturas", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def crear_factura_individual(
    factura_in: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Crea una factura individual con validación mejorada.
    
    Cambios implementados:
    - Schemas con validación automática
    - Excepciones personalizadas
    - Repository pattern
    """

    # 1. Validar que no exista referencia duplicada
    factura_repo = FacturaRepository(session)
    existing = await factura_repo.get_by_reference_code(factura_in.reference_code)
    
    if existing:
        raise ConflictException(
            f"Invoice with reference code '{factura_in.reference_code}' already exists"
        )

    # 2. Validar datos de negocio
    errors = []
    for item in factura_in.items:
        if item.quantity <= 0:
            errors.append(f"Invalid quantity ({item.quantity}) for item {item.name}")
        if item.price < 0:
            errors.append(f"Invalid price ({item.price}) for item {item.name}")
    
    if errors:
        raise ValidationException(errors)

    # 3. Calcular totales
    total_bruto = 0.0
    total_impuestos = 0.0
    items_transformados = []

    for item in factura_in.items:
        subtotal_linea = item.price * item.quantity
        impuesto_linea = subtotal_linea * (item.tax_rate / 100)

        total_bruto += subtotal_linea
        total_impuestos += impuesto_linea

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
                    "amount": impuesto_linea,
                }
            ],
        }
        items_transformados.append(item_struct)

    # 4. Construir payload para API Factus
    factura_payload = {
        "numbering_range_id": factura_in.numbering_range_id,
        "reference_code": factura_in.reference_code,
        "observation": factura_in.observation,
        "payment_form": factura_in.payment_form,
        "payment_method_code": factura_in.payment_method_code,
        "customer": factura_in.customer.dict(),
        "items": items_transformados,
    }

    # 5. Enviar a Factus API
    resultado_api = await factus_client.enviar_factura(factura_payload)

    es_exito = resultado_api.get("status") in [200, 201]
    estado_final = "ENVIADA" if es_exito else "ERROR_API"
    motivo = None
    if not es_exito:
        motivo = f"API Error: {resultado_api.get('status')} - {resultado_api.get('error', '')}"

    # 6. Guardar en BD usando repository
    nueva_factura = Factura(
        reference_code=factura_in.reference_code,
        cliente_email=factura_in.customer.email,
        total=total_bruto + total_impuestos,
        estado=estado_final,
        motivo_rechazo=motivo,
        api_response=resultado_api,
        lote_id=None,
    )

    factura_guardada = await factura_repo.create(nueva_factura)

    # 7. Retornar respuesta transformada
    return InvoiceResponse(
        id=factura_guardada.id,
        reference_code=factura_guardada.reference_code,
        cliente_email=factura_guardada.cliente_email,
        total=factura_guardada.total,
        estado=factura_guardada.estado,
        motivo_rechazo=factura_guardada.motivo_rechazo,
        factus_response=factura_guardada.api_response,
    )


@router.get("/facturas/{invoice_id}", response_model=InvoiceResponse)
async def obtener_factura(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Obtener factura por ID"""
    factura_repo = FacturaRepository(session)
    factura = await factura_repo.get(invoice_id)

    if not factura:
        raise NotFoundException("Invoice", invoice_id)

    return InvoiceResponse(
        id=factura.id,
        reference_code=factura.reference_code,
        cliente_email=factura.cliente_email,
        total=factura.total,
        estado=factura.estado,
        motivo_rechazo=factura.motivo_rechazo,
        factus_response=factura.api_response,
    )


@router.get("/facturas/cliente/{email}", response_model=InvoiceListResponse)
async def obtener_facturas_cliente(
    email: str,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Obtener facturas de un cliente con paginación"""
    if page < 1 or page_size < 1:
        raise ValidationException(["page and page_size must be positive"])

    factura_repo = FacturaRepository(session)
    skip = (page - 1) * page_size

    facturas = await factura_repo.get_by_cliente_email(
        email=email, skip=skip, limit=page_size
    )
    total = await factura_repo.count(cliente_email=email)

    items = [
        InvoiceResponse(
            id=f.id,
            reference_code=f.reference_code,
            cliente_email=f.cliente_email,
            total=f.total,
            estado=f.estado,
            motivo_rechazo=f.motivo_rechazo,
            factus_response=f.api_response,
        )
        for f in facturas
    ]

    pages = (total + page_size - 1) // page_size

    return InvoiceListResponse(
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )
