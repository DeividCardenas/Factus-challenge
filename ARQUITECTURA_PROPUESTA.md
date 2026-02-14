# 🏗️ Arquitectura Propuesta - Factus Challenge

## 📁 Nueva Estructura de Carpetas

```
factus-challenge/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Entry point
│   │
│   ├── api/                         # ⭐ NUEVA: Capa de presentación
│   │   ├── __init__.py
│   │   ├── deps.py                  # Dependencias globales
│   │   ├── errors/                  # Manejo de errores
│   │   │   ├── __init__.py
│   │   │   ├── handlers.py          # Exception handlers
│   │   │   └── http_errors.py       # Custom exceptions
│   │   │
│   │   └── v1/                      # ⭐ Versionado de API
│   │       ├── __init__.py
│   │       ├── router.py            # Router principal v1
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── documents.py
│   │           ├── invoices.py
│   │           └── health.py        # Health checks
│   │
│   ├── core/                        # ⭐ Configuración central
│   │   ├── __init__.py
│   │   ├── config.py                # Mejorado con Pydantic Settings
│   │   ├── security.py
│   │   ├── logging.py               # ⭐ NUEVO: Logging estructurado
│   │   ├── events.py                # ⭐ NUEVO: Startup/shutdown events
│   │   └── celery_app.py
│   │
│   ├── models/                      # ⭐ NUEVO: Modularizado
│   │   ├── __init__.py
│   │   ├── base.py                  # Base classes
│   │   ├── user.py
│   │   ├── lote.py
│   │   └── factura.py
│   │
│   ├── schemas/                     # ⭐ NUEVO: Pydantic schemas (DTOs)
│   │   ├── __init__.py
│   │   ├── auth.py                  # Login, Token schemas
│   │   ├── invoice.py               # Request/Response schemas
│   │   ├── lote.py
│   │   └── common.py                # Schemas compartidos
│   │
│   ├── repositories/                # ⭐ NUEVO: Capa de acceso a datos
│   │   ├── __init__.py
│   │   ├── base.py                  # Base Repository (CRUD genérico)
│   │   ├── user_repository.py
│   │   ├── lote_repository.py
│   │   └── factura_repository.py
│   │
│   ├── services/                    # ⭐ MEJORADO: Lógica de negocio
│   │   ├── __init__.py
│   │   ├── auth_service.py          # ⭐ NUEVO: Login, JWT
│   │   ├── invoice_service.py       # ⭐ NUEVO: Crear facturas
│   │   ├── lote_service.py          # ⭐ NUEVO: Procesar lotes
│   │   ├── transformer.py           # Ya existe (Polars)
│   │   └── api_client.py            # Ya existe (Factus API)
│   │
│   ├── tasks/                       # ⭐ NUEVO: Celery tasks modularizado
│   │   ├── __init__.py
│   │   ├── invoice_tasks.py
│   │   └── lote_tasks.py
│   │
│   ├── db/                          # ⭐ NUEVO: Database management
│   │   ├── __init__.py
│   │   ├── base.py                  # Base setup
│   │   ├── session.py               # Session management
│   │   └── migrations/              # Alembic migrations
│   │
│   ├── graphql/                     # Ya existe (mejorar)
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── types.py
│   │   └── resolvers/               # ⭐ NUEVO: Separar resolvers
│   │       ├── __init__.py
│   │       ├── lote_resolvers.py
│   │       └── factura_resolvers.py
│   │
│   └── utils/                       # ⭐ NUEVO: Utilidades
│       ├── __init__.py
│       ├── validators.py            # Validaciones custom
│       ├── formatters.py            # Formateo de datos
│       └── constants.py             # Constantes globales
│
├── tests/                           # ⭐ NUEVO: Testing completo
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures pytest
│   ├── unit/
│   │   ├── test_services.py
│   │   ├── test_repositories.py
│   │   └── test_utils.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   └── test_celery_tasks.py
│   └── e2e/
│       └── test_invoice_flow.py
│
├── alembic/                         # ⭐ NUEVO: Migraciones de BD
│   ├── versions/
│   └── env.py
│
├── docs/                            # ⭐ NUEVO: Documentación
│   ├── api.md
│   ├── database.md
│   └── deployment.md
│
├── scripts/                         # ⭐ NUEVO: Scripts de utilidad
│   ├── init_db.py
│   ├── seed_data.py
│   └── run_tests.sh
│
├── .env.example                     # Template de configuración
├── .env.local
├── .env.production
├── docker-compose.yml
├── docker-compose.prod.yml          # ⭐ NUEVO: Prod compose
├── Dockerfile                       # ⭐ NUEVO: Containerización
├── pytest.ini                       # ⭐ NUEVO: Config pytest
├── alembic.ini                      # ⭐ NUEVO: Config migraciones
└── requirements.txt

```

---

## 🎯 Principios de la Nueva Arquitectura

### 1. **Clean Architecture / Hexagonal**
```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│  ┌─────────────────────────────────┐   │
│  │   Endpoints (REST + GraphQL)    │   │
│  └──────────────┬──────────────────┘   │
│                 │                        │
│  ┌──────────────▼──────────────────┐   │
│  │   Services (Business Logic)     │   │
│  └──────────────┬──────────────────┘   │
│                 │                        │
│  ┌──────────────▼──────────────────┐   │
│  │   Repositories (Data Access)    │   │
│  └──────────────┬──────────────────┘   │
│                 │                        │
│  ┌──────────────▼──────────────────┐   │
│  │   Models (Database Entities)    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 2. **Dependency Injection**
- Todos los servicios se inyectan vía FastAPI Depends
- Facilita testing con mocks
- Desacoplamiento total

### 3. **Domain-Driven Design (DDD)**
- Modelos de dominio ricos
- Servicios por contexto de negocio
- Repositorios abstractos

### 4. **Single Responsibility**
- Cada capa tiene una responsabilidad
- Endpoints solo validan y delegan
- Services contienen lógica de negocio
- Repositories solo acceso a datos

---

## 🛠️ Mejoras Técnicas Específicas

### 1. **Configuración Avanzada (Pydantic Settings)**
```python
# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Factus API"
    APP_VERSION: str = "1.0.0"
    APP_MODE: str = "development"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS384"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Factus API
    FACTUS_URL: str
    FACTUS_TOKEN: str
    FACTUS_TIMEOUT: int = 30
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 2. **Exception Handling Centralizado**
```python
# app/api/errors/http_errors.py
class APIException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code

class NotFoundException(APIException):
    def __init__(self, resource: str, id: any):
        super().__init__(
            status_code=404,
            detail=f"{resource} with id {id} not found",
            error_code="NOT_FOUND"
        )

class ValidationException(APIException):
    def __init__(self, errors: list):
        super().__init__(
            status_code=422,
            detail="Validation failed",
            error_code="VALIDATION_ERROR"
        )
        self.errors = errors
```

### 3. **Base Repository Pattern**
```python
# app/repositories/base.py
from typing import Generic, TypeVar, Type, Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get(self, id: int) -> Optional[ModelType]:
        return await self.session.get(self.model, id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def update(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False
```

### 4. **Service Layer con Lógica de Negocio**
```python
# app/services/invoice_service.py
from app.repositories.factura_repository import FacturaRepository
from app.services.api_client import FactusService
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.api.errors.http_errors import ValidationException

class InvoiceService:
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
        # Validación de negocio
        self._validate_invoice(invoice_data)
        
        # Calcular totales
        totals = self._calculate_totals(invoice_data)
        
        # Enviar a Factus API
        api_response = await self.factus_client.enviar_factura(
            self._transform_to_factus_format(invoice_data, totals)
        )
        
        # Guardar en BD
        invoice = await self.factura_repo.create_from_schema(
            invoice_data, 
            api_response,
            totals
        )
        
        return InvoiceResponse.from_orm(invoice)
    
    def _validate_invoice(self, data: InvoiceCreate):
        errors = []
        
        if not data.items:
            errors.append("Invoice must have at least one item")
        
        for item in data.items:
            if item.quantity <= 0:
                errors.append(f"Invalid quantity for {item.name}")
            if item.price < 0:
                errors.append(f"Invalid price for {item.name}")
        
        if errors:
            raise ValidationException(errors)
```

### 5. **Logging Estructurado**
```python
# app/core/logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log(self, level: str, message: str, **context):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **context
        }
        getattr(self.logger, level)(json.dumps(log_data))
    
    def info(self, message: str, **context):
        self.log("info", message, **context)
    
    def error(self, message: str, **context):
        self.log("error", message, **context)
```

### 6. **Testing Completo**
```python
# tests/conftest.py
import pytest
from sqlmodel import create_engine, SQLModel
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(name="session")
async def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

---

## 📊 Mejoras de Performance

### 1. **Caché con Redis**
```python
from redis import asyncio as aioredis
from functools import wraps

cache = aioredis.from_url("redis://localhost")

def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            cached_value = await cache.get(key)
            
            if cached_value:
                return json.loads(cached_value)
            
            result = await func(*args, **kwargs)
            await cache.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 2. **Connection Pooling Optimizado**
```python
# Configuración engine con pool optimizado para alta carga
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=50,              # Conexiones permanentes
    max_overflow=20,           # Conexiones extra bajo carga
    pool_pre_ping=True,        # Verifica conexiones antes de usar
    pool_recycle=3600,         # Recicla conexiones cada hora
    connect_args={
        "server_settings": {
            "jit": "on",       # JIT en PostgreSQL
            "application_name": "factus_api"
        }
    }
)
```

### 3. **Background Tasks Optimizados**
```python
# Usar FastAPI BackgroundTasks para tareas cortas
@router.post("/factura")
async def crear_factura(
    data: InvoiceCreate,
    background_tasks: BackgroundTasks
):
    invoice = await service.create_invoice(data)
    
    # Tarea en background (no bloqueante)
    background_tasks.add_task(
        send_email_notification,
        invoice.cliente_email
    )
    
    return invoice
```

---

## 🔐 Seguridad Mejorada

### 1. **Rate Limiting**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # 5 intentos por minuto
async def login(request: Request, ...):
    ...
```

### 2. **CORS Configurado**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. **Helmet-style Security Headers**
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## 📈 Métricas y Monitoreo

### 1. **Prometheus Metrics**
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 2. **Health Checks**
```python
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_session)):
    return {
        "status": "healthy",
        "database": await check_db_connection(db),
        "redis": await check_redis_connection(),
        "celery": await check_celery_workers()
    }
```

---

## 🚢 Deployment

### Docker Multi-Stage
```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY ./app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Ready
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: factus-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: factus-api
  template:
    spec:
      containers:
      - name: api
        image: factus-api:latest
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## 📝 Checklist de Implementación

### Fase 1: Refactorización Base (1-2 semanas)
- [ ] Crear estructura de carpetas nueva
- [ ] Implementar BaseRepository
- [ ] Crear Services layer
- [ ] Migrar endpoints a nueva estructura
- [ ] Implementar manejo de errores
- [ ] Configurar logging

### Fase 2: Testing y Calidad (1 semana)
- [ ] Setup pytest
- [ ] Tests unitarios (services)
- [ ] Tests de integración (API)
- [ ] Tests de Celery tasks
- [ ] Coverage > 80%

### Fase 3: Performance (1 semana)
- [ ] Implementar caché Redis
- [ ] Optimizar queries (índices)
- [ ] Background tasks optimizados
- [ ] Stress testing con Locust

### Fase 4: Seguridad y Deployment (1 semana)
- [ ] Rate limiting
- [ ] CORS y security headers
- [ ] Alembic migrations
- [ ] Docker compose producción
- [ ] CI/CD pipeline

---

## 🎯 Beneficios de la Nueva Arquitectura

1. **Escalabilidad Horizontal**: Fácil replicar instancias
2. **Mantenibilidad**: Código organizado y desacoplado
3. **Testeable**: 100% coverage posible
4. **Performance**: Caché + pool optimizado + async
5. **Seguridad**: Multiple capas de protección
6. **Observabilidad**: Logs + métricas + health checks
7. **Deployment**: Docker + K8s ready
8. **Extensibilidad**: Agregar features sin romper existentes

---

## 🚀 Próximos Pasos

¿Por dónde empezamos? Te recomiendo:

1. **Fase 1 Prioritaria**: Repositories + Services
2. **Quick Win**: Logging estructurado (mejora debug inmediato)
3. **Critical**: Exception handling (mejora UX)
