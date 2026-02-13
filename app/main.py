from fastapi import FastAPI, Depends
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.routers import documents, auth, invoices
from app.core.config import settings
from app.database import init_db, get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator

# 1. Inicializar App
app = FastAPI(
    title="Factus Challenge API",
    version="1.0.0",
    description="API de Facturación LOCAL - Modo Simulación",
    debug=settings.DEBUG
)

# --- EVENTO DE INICIO ---
@app.on_event("startup")
async def on_startup():
    # Esto crea las tablas en Postgres si no existen y el usuario admin
    await init_db()
    print("🚀 Base de Datos PostgreSQL conectada y tablas creadas.")

# --- CONTEXT GETTER PARA GRAPHQL ---
async def get_context(
    db: AsyncSession = Depends(get_session)
):
    """
    Inyecta la sesión de DB en el contexto de GraphQL.
    Strawberry automáticamente ejecuta esto y pasa el resultado a info.context.
    """
    return {
        "db": db
    }

# 2. Conectar Router de GraphQL con Contexto
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

# 3. Conectar Routers REST
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(documents.router, tags=["Documentos"])
app.include_router(invoices.router, tags=["Facturas Individuales"])

@app.get("/")
def home():
    return {
        "mensaje": "🚀 API Factus Challenge - MODO LOCAL ACTIVADO",
        "ambiente": settings.APP_MODE,
        "documentacion": "/docs",
        "endpoints": {
            "graphql": "/graphql",
            "login": "POST /auth/login",
            "procesar_documento": "POST /procesar-documento",
            "emitir_masivas": "POST /emitir-facturas-masivas (Protegido)",
            "emitir_individual": "POST /facturas (Protegido)"
        }
    }
