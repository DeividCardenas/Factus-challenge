"""GraphQL Module - API GraphQL integrada con servicios compartidos"""

from app.graphql.types import (
    InvoiceType, InvoiceListType, LoteType, LoteListType,
    LoteDetailType, LoteStatisticsType, UserType, AuthResponseType,
    SimpleInvoiceType,
    EstadoFactura, EstadoLote
)
from app.graphql.inputs import (
    InvoiceCreateInput, InvoiceUpdateInput,
    LoteCreateInput, LoteUpdateInput,
    CustomerInput, ItemInput,
    PaginationInput, LoginInput
)
from app.graphql.queries import Query
from app.graphql.schema import schema

__all__ = [
    # Types
    "InvoiceType", "InvoiceListType", "SimpleInvoiceType",
    "LoteType", "LoteListType", "LoteDetailType",
    "LoteStatisticsType", "UserType", "AuthResponseType",
    "EstadoFactura", "EstadoLote",
    
    # Inputs
    "InvoiceCreateInput", "InvoiceUpdateInput",
    "LoteCreateInput", "LoteUpdateInput",
    "CustomerInput", "ItemInput",
    "PaginationInput", "LoginInput",
    
    # Query & Schema
    "Query", "schema",
]
