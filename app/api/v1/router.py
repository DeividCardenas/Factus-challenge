from fastapi import APIRouter
from app.api.v1.endpoints import auth, documents, invoices

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(documents.router, tags=["Documentos"])
api_router.include_router(invoices.router, tags=["Facturas Individuales"])
