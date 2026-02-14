from fastapi import FastAPI, Depends, Request
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db, get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator, Optional, Dict, Any
from app.api.errors.handlers import setup_exception_handlers
from app.core.deps import get_current_user
from app.models import User

# 1. Inicializar App
app = FastAPI(
    title="Factus Challenge API",
    version="1.0.0",
    description="API de Facturación LOCAL - Modo Simulación",
    debug=settings.DEBUG
)

# 2. Configurar exception handlers
setup_exception_handlers(app)

# --- EVENTO DE INICIO ---
@app.on_event("startup")
async def on_startup():
    """Inicialización de la aplicación"""
    # Esto crea las tablas en Postgres si no existen y el usuario admin
    await init_db()
    print("🚀 Base de Datos PostgreSQL conectada y tablas creadas.")
    print("✅ Exception handlers configurados")
    print("📊 GraphQL habilitado en /graphql")
    print("📚 REST API habilitado en /docs")


# --- CONTEXT GETTER PARA GRAPHQL CON INYECCIÓN DE DEPENDENCIAS ---
async def get_graphql_context(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """
    Contexto para GraphQL con:
    - Sesión de base de datos
    - Usuario actual (si está autenticado)
    - Request object
    
    GraphQL pasará esto a info.context en cada resolver.
    """
    user: Optional[User] = None
    
    # Intentar obtener usuario del header Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            # Extraer token y validar
            token = auth_header.replace("Bearer ", "")
            user = await get_current_user(token, db)
        except Exception:
            # Si falla validación, continuar sin usuario
            pass
    
    return {
        "session": db,
        "user": user,
        "request": request
    }


# 3. Conectar Router de GraphQL con Contexto Mejorado
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_graphql_context
)
app.include_router(graphql_app, prefix="/graphql")

# 4. Conectar Routers REST
# Agregamos el router de la versión 1 con prefijo /api/v1
app.include_router(api_router, prefix="/api/v1")


# --- HEALTH CHECK ---
@app.get("/health")
async def health_check():
    """Verificar estado de la API"""
    return {
        "status": "healthy",
        "graphql_endpoint": "/graphql",
        "docs_endpoint": "/docs",
        "graphql_docs_endpoint": "/graphql/schema"
    }


@app.get("/")
def home():
    return {
        "mensaje": "🚀 API Factus Challenge - MODO LOCAL ACTIVADO",
        "ambiente": settings.APP_MODE,
        "documentacion": "/docs",
        "endpoints": {
            "graphql": "/graphql",
            "login": "POST /api/v1/auth/login",
            "procesar_documento": "POST /api/v1/procesar-documento",
            "emitir_masivas": "POST /api/v1/emitir-facturas-masivas (Protegido)",
            "emitir_individual": "POST /api/v1/facturas (Protegido)"
        }
    }
