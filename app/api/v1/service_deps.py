"""
Inyección de Dependencias para Services

Este módulo proporciona funciones para inyectar servicios en endpoints.
Usa FastAPI Depends para que la inyección sea automática y testeable.
"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.services.invoice_service import InvoiceService
from app.services.auth_service import AuthService
from app.services.lote_service import LoteService


async def get_invoice_service(
    session: AsyncSession = Depends(get_session)
) -> InvoiceService:
    """
    Inyecta InvoiceService en endpoints.
    
    Uso en endpoints:
        @router.get("/facturas/{id}")
        async def get_invoice(
            invoice_service: InvoiceService = Depends(get_invoice_service)
        ):
            return await invoice_service.obtener_factura(id)
    """
    return InvoiceService(session)


async def get_auth_service(
    session: AsyncSession = Depends(get_session)
) -> AuthService:
    """
    Inyecta AuthService en endpoints.
    """
    return AuthService(session)


async def get_lote_service(
    session: AsyncSession = Depends(get_session)
) -> LoteService:
    """
    Inyecta LoteService en endpoints.
    """
    return LoteService(session)
