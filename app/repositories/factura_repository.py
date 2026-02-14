"""Factura Repository"""

from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Factura
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    """Repositorio especializado para Facturas"""

    def __init__(self, session: AsyncSession):
        super().__init__(Factura, session)

    async def get_by_reference_code(self, ref_code: str) -> Optional[Factura]:
        """Buscar factura por código de referencia"""
        query = select(Factura).where(Factura.reference_code == ref_code)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_lote(
        self, lote_id: int, estado: Optional[str] = None
    ) -> List[Factura]:
        """Obtener facturas de un lote con filtro opcional de estado"""
        query = select(Factura).where(Factura.lote_id == lote_id)

        if estado:
            query = query.where(Factura.estado == estado)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_cliente_email(
        self, email: str, skip: int = 0, limit: int = 50
    ) -> List[Factura]:
        """Obtener facturas de un cliente con paginación"""
        query = (
            select(Factura)
            .where(Factura.cliente_email == email)
            .order_by(Factura.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_estadisticas_lote(self, lote_id: int) -> dict:
        """Calcular estadísticas de un lote"""
        from sqlalchemy import func

        query = (
            select(
                Factura.estado,
                func.count(Factura.id).label("total"),
                func.sum(Factura.total).label("monto_total"),
            )
            .where(Factura.lote_id == lote_id)
            .group_by(Factura.estado)
        )

        result = await self.session.execute(query)
        rows = result.all()

        estadisticas = {
            "total_facturas": 0,
            "total_enviadas": 0,
            "total_rechazadas": 0,
            "total_pendientes": 0,
            "monto_total": 0.0,
            "monto_exitoso": 0.0,
        }

        for estado, total, monto in rows:
            estadisticas["total_facturas"] += total
            estadisticas["monto_total"] += monto or 0.0

            if estado == "ENVIADA":
                estadisticas["total_enviadas"] = total
                estadisticas["monto_exitoso"] = monto or 0.0
            elif estado == "RECHAZADA":
                estadisticas["total_rechazadas"] = total
            elif estado == "PENDIENTE":
                estadisticas["total_pendientes"] = total

        return estadisticas

    async def bulk_create(self, facturas: List[Factura]) -> List[Factura]:
        """Crear múltiples facturas eficientemente"""
        self.session.add_all(facturas)
        await self.session.commit()

        for factura in facturas:
            await self.session.refresh(factura)

        return facturas

    async def update_estado(
        self,
        factura_id: int,
        nuevo_estado: str,
        motivo: Optional[str] = None,
        api_response: Optional[dict] = None,
    ) -> Optional[Factura]:
        """Actualizar estado de factura con información adicional"""
        factura = await self.get(factura_id)

        if not factura:
            return None

        factura.estado = nuevo_estado

        if motivo:
            factura.motivo_rechazo = motivo

        if api_response:
            factura.api_response = api_response

        return await self.update(factura)
