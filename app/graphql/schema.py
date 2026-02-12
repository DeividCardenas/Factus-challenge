import strawberry
from typing import List
from app.services.api_client import factus_client
from app.graphql.types import EstadoConexion, FacturaTransformada, ClienteFactura, ItemFactura


@strawberry.type
class Query:
    @strawberry.field
    async def verificar_conexion_factus(self) -> EstadoConexion:
        resultado = await factus_client.verificar_estado_api()
        return EstadoConexion(
            codigo=resultado["codigo"],
            mensaje=resultado["mensaje"],
            data=resultado["data"]
        )

schema = strawberry.Schema(query=Query)