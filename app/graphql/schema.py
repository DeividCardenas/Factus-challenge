import strawberry
from typing import List, Optional
from strawberry.types import Info
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models import Lote, Factura

# Importamos los tipos y definimos las clases Strawberry
# PERO, el schema anterior tenía un bug circular o importación:
# `LoteType` en `schema.py` referenciaba `FacturaType` y ambos deben ser accesibles.
# Para simplificar y evitar problemas de scope, vamos a definirlos aquí o importar
# y asegurar que la conversión sea correcta.

# En `app/graphql/types.py` definimos `FacturaType` y `LoteType`.
# Sin embargo, `LoteType` necesita una lista de `FacturaType`.
# Si importamos desde `types.py`, está bien.

from app.graphql.types import LoteType, FacturaType

@strawberry.type
class Query:
    @strawberry.field
    async def historial_lotes(self, info: Info) -> List[LoteType]:
        session = info.context["db"]
        # Usamos selectinload para cargar facturas de forma eficiente (1 query extra)
        statement = select(Lote).order_by(Lote.fecha_carga.desc()).options(selectinload(Lote.facturas))
        result = await session.exec(statement)
        lotes = result.all()

        # Mapeo manual para asegurar tipos
        mapped_lotes = []
        for l in lotes:
            mapped_facturas = [
                FacturaType(
                    id=f.id,
                    reference_code=f.reference_code,
                    cliente_email=f.cliente_email,
                    total=f.total,
                    estado=f.estado,
                    motivo_rechazo=f.motivo_rechazo,
                    api_response=f.api_response
                ) for f in l.facturas
            ]
            mapped_lotes.append(
                LoteType(
                    id=l.id,
                    nombre_archivo=l.nombre_archivo,
                    fecha_carga=l.fecha_carga,
                    total_registros=l.total_registros,
                    total_errores=l.total_errores,
                    estado=l.estado,
                    facturas=mapped_facturas
                )
            )
        return mapped_lotes

    @strawberry.field
    async def detalle_lote(self, info: Info, id: strawberry.ID) -> Optional[LoteType]:
        session = info.context["db"]
        statement = select(Lote).where(Lote.id == int(id)).options(selectinload(Lote.facturas))
        result = await session.exec(statement)
        lote = result.first()

        if not lote:
            return None

        mapped_facturas = [
            FacturaType(
                id=f.id,
                reference_code=f.reference_code,
                cliente_email=f.cliente_email,
                total=f.total,
                estado=f.estado,
                motivo_rechazo=f.motivo_rechazo,
                api_response=f.api_response
            ) for f in lote.facturas
        ]

        return LoteType(
            id=lote.id,
            nombre_archivo=lote.nombre_archivo,
            fecha_carga=lote.fecha_carga,
            total_registros=lote.total_registros,
            total_errores=lote.total_errores,
            estado=lote.estado,
            facturas=mapped_facturas
        )

schema = strawberry.Schema(query=Query)
