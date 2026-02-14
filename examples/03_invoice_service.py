# Service Layer - Lógica de Negocio Separada

from typing import List, Optional
from app.models import Factura
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceStats
from examples.factura_repository import FacturaRepository
from app.services.api_client import FactusService
from app.api.errors.http_errors import ValidationException, NotFoundException

class InvoiceService:
    """
    Servicio de lógica de negocio para facturas.
    
    Responsabilidades:
    - Validar reglas de negocio
    - Orquestar operaciones complejas
    - Coordinar con servicios externos
    - Transformar entre DTOs y modelos
    
    NO hace queries directamente - usa repositories
    """
    
    def __init__(
        self,
        factura_repo: FacturaRepository,
        factus_client: FactusService
    ):
        self.factura_repo = factura_repo
        self.factus_client = factus_client
    
    async def create_invoice(
        self, 
        invoice_data: InvoiceCreate,
        user_id: int
    ) -> InvoiceResponse:
        """
        Crear y enviar una factura individual.
        
        Flujo:
        1. Validar datos de negocio
        2. Calcular totales
        3. Enviar a API Factus
        4. Guardar resultado en BD
        5. Retornar respuesta transformada
        """
        
        # 1. Validación de negocio
        self._validate_invoice_data(invoice_data)
        
        # 2. Verificar duplicados
        existing = await self.factura_repo.get_by_reference_code(
            invoice_data.reference_code
        )
        if existing:
            raise ValidationException([
                f"Invoice with reference {invoice_data.reference_code} already exists"
            ])
        
        # 3. Calcular totales
        totals = self._calculate_totals(invoice_data)
        
        # 4. Transformar a formato Factus
        factus_payload = self._transform_to_factus_format(invoice_data, totals)
        
        # 5. Enviar a API externa
        api_response = await self.factus_client.enviar_factura(factus_payload)
        
        # 6. Determinar estado según respuesta
        es_exitosa = api_response.get("status") in [200, 201]
        estado = "ENVIADA" if es_exitosa else "ERROR_API"
        motivo_rechazo = None if es_exitosa else api_response.get("error", "Unknown error")
        
        # 7. Crear modelo de BD
        nueva_factura = Factura(
            reference_code=invoice_data.reference_code,
            cliente_email=invoice_data.customer.email,
            total=totals["total_con_iva"],
            estado=estado,
            motivo_rechazo=motivo_rechazo,
            api_response=api_response,
            lote_id=None  # Factura individual
        )
        
        # 8. Guardar en BD
        factura_guardada = await self.factura_repo.create(nueva_factura)
        
        # 9. Transformar a DTO de respuesta
        return InvoiceResponse(
            id=factura_guardada.id,
            reference_code=factura_guardada.reference_code,
            cliente_email=factura_guardada.cliente_email,
            total=factura_guardada.total,
            estado=factura_guardada.estado,
            motivo_rechazo=factura_guardada.motivo_rechazo,
            created_at=factura_guardada.id,  # Puedes agregar timestamp al modelo
            factus_response=api_response
        )
    
    async def get_invoice_by_id(self, invoice_id: int) -> InvoiceResponse:
        """Obtener factura por ID"""
        factura = await self.factura_repo.get(invoice_id)
        
        if not factura:
            raise NotFoundException("Invoice", invoice_id)
        
        return InvoiceResponse.from_orm(factura)
    
    async def get_invoice_by_reference(self, reference: str) -> InvoiceResponse:
        """Obtener factura por código de referencia"""
        factura = await self.factura_repo.get_by_reference_code(reference)
        
        if not factura:
            raise NotFoundException("Invoice", reference)
        
        return InvoiceResponse.from_orm(factura)
    
    async def get_client_invoices(
        self,
        email: str,
        page: int = 1,
        page_size: int = 50
    ) -> List[InvoiceResponse]:
        """Obtener facturas de un cliente con paginación"""
        skip = (page - 1) * page_size
        
        facturas = await self.factura_repo.get_by_cliente_email(
            email=email,
            skip=skip,
            limit=page_size
        )
        
        return [InvoiceResponse.from_orm(f) for f in facturas]
    
    async def get_lote_statistics(self, lote_id: int) -> InvoiceStats:
        """Obtener estadísticas de un lote"""
        stats = await self.factura_repo.get_estadisticas_lote(lote_id)
        
        return InvoiceStats(
            total_count=stats["total_facturas"],
            successful_count=stats["total_enviadas"],
            failed_count=stats["total_rechazadas"],
            pending_count=stats["total_pendientes"],
            total_amount=stats["monto_total"],
            successful_amount=stats["monto_exitoso"],
            success_rate=(
                stats["total_enviadas"] / stats["total_facturas"] * 100
                if stats["total_facturas"] > 0 else 0
            )
        )
    
    async def retry_failed_invoice(self, invoice_id: int) -> InvoiceResponse:
        """Reintentar envío de factura fallida"""
        factura = await self.factura_repo.get(invoice_id)
        
        if not factura:
            raise NotFoundException("Invoice", invoice_id)
        
        if factura.estado == "ENVIADA":
            raise ValidationException(["Invoice already sent successfully"])
        
        # Reconstruir payload y reenviar
        # (necesitarías guardar más info o reconstruir desde api_response)
        # Por ahora simplificado:
        
        api_response = await self.factus_client.enviar_factura({
            "reference_code": factura.reference_code,
            # ... resto de datos
        })
        
        # Actualizar estado
        es_exitosa = api_response.get("status") in [200, 201]
        nuevo_estado = "ENVIADA" if es_exitosa else "ERROR_API"
        
        await self.factura_repo.update_estado(
            factura_id=invoice_id,
            nuevo_estado=nuevo_estado,
            api_response=api_response
        )
        
        return await self.get_invoice_by_id(invoice_id)
    
    # --- MÉTODOS PRIVADOS DE VALIDACIÓN ---
    
    def _validate_invoice_data(self, data: InvoiceCreate):
        """Validar reglas de negocio"""
        errors = []
        
        if not data.items or len(data.items) == 0:
            errors.append("Invoice must have at least one item")
        
        for item in data.items:
            if item.quantity <= 0:
                errors.append(f"Invalid quantity ({item.quantity}) for item {item.name}")
            
            if item.price < 0:
                errors.append(f"Invalid price ({item.price}) for item {item.name}")
            
            if item.tax_rate < 0 or item.tax_rate > 100:
                errors.append(f"Invalid tax rate ({item.tax_rate}) for item {item.name}")
        
        if errors:
            raise ValidationException(errors)
    
    def _calculate_totals(self, data: InvoiceCreate) -> dict:
        """Calcular totales de la factura"""
        total_bruto = 0.0
        total_impuestos = 0.0
        total_descuentos = 0.0
        
        for item in data.items:
            subtotal = item.price * item.quantity
            descuento = subtotal * (item.discount_rate / 100)
            base_imponible = subtotal - descuento
            impuesto = base_imponible * (item.tax_rate / 100)
            
            total_bruto += subtotal
            total_descuentos += descuento
            total_impuestos += impuesto
        
        return {
            "total_bruto": total_bruto,
            "total_descuentos": total_descuentos,
            "total_impuestos": total_impuestos,
            "total_con_iva": total_bruto - total_descuentos + total_impuestos
        }
    
    def _transform_to_factus_format(self, data: InvoiceCreate, totals: dict) -> dict:
        """Transformar a formato de API Factus"""
        items_transformados = []
        
        for item in data.items:
            subtotal = item.price * item.quantity
            descuento = subtotal * (item.discount_rate / 100)
            base_imponible = subtotal - descuento
            impuesto = base_imponible * (item.tax_rate / 100)
            
            items_transformados.append({
                "code_reference": item.code_reference,
                "name": item.name,
                "quantity": item.quantity,
                "price": item.price,
                "tax_rate": item.tax_rate,
                "discount_rate": item.discount_rate,
                "taxes": [{
                    "code": "1",
                    "name": "IVA",
                    "rate": item.tax_rate,
                    "amount": impuesto
                }]
            })
        
        return {
            "numbering_range_id": data.numbering_range_id,
            "reference_code": data.reference_code,
            "observation": data.observation,
            "payment_form": data.payment_form,
            "payment_method_code": data.payment_method_code,
            "customer": data.customer.dict(),
            "items": items_transformados
        }


# --- DEPENDENCY INJECTION EN ENDPOINT ---

async def get_invoice_service(
    session: AsyncSession = Depends(get_session)
) -> InvoiceService:
    """Factory para inyectar InvoiceService con dependencias"""
    factura_repo = FacturaRepository(session)
    factus_client = FactusService()
    return InvoiceService(factura_repo, factus_client)


# --- USO EN ENDPOINT ---

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models import User

router = APIRouter()

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Endpoint simplificado - toda la lógica está en el service.
    El endpoint solo valida, delega y retorna.
    """
    return await invoice_service.create_invoice(invoice_data, current_user.id)

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    return await invoice_service.get_invoice_by_id(invoice_id)

@router.get("/invoices/reference/{reference}", response_model=InvoiceResponse)
async def get_invoice_by_reference(
    reference: str,
    current_user: User = Depends(get_current_user),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    return await invoice_service.get_invoice_by_reference(reference)

@router.post("/invoices/{invoice_id}/retry", response_model=InvoiceResponse)
async def retry_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    return await invoice_service.retry_failed_invoice(invoice_id)
