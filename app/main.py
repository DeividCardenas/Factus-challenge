from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.routers import documents
from app.core.config import settings
from app.database import init_db

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
    # Esto crea las tablas en Postgres si no existen
    await init_db()
    print("🚀 Base de Datos PostgreSQL conectada y tablas creadas.")

# 2. Conectar Router de GraphQL
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# 3. Conectar Router de Documentos (REST)
app.include_router(documents.router, tags=["Documentos"])

@app.get("/")
def home():
    return {
        "mensaje": "🚀 API Factus Challenge - MODO LOCAL ACTIVADO",
        "ambiente": settings.APP_MODE,
        "endpoints": {
            "graphql": "/graphql",
            "procesar_documento": "POST /procesar-documento",
            "emitir_masivas": "POST /emitir-facturas-masivas"
        }
    }