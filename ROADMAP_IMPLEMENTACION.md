# 🚀 ROADMAP DE IMPLEMENTACIÓN PASO A PASO

## 📋 Fases y Timeline Estimado

### FASE 1: SETUP Y CONFIGURACIÓN (2-3 días)

#### 1.1 Actualizar requirements.txt con nuevas dependencias
```bash
# Agregar a requirements.txt
pydantic-settings>=2.0.0       # Configuración avanzada
pytest>=7.0.0                  # Testing
pytest-asyncio>=0.21.0         # Tests async
sqlalchemy-utils>=0.41.1       # Utilidades SQL
python-multipart>=0.0.6        # Ya tienen
```

#### 1.2 Restructurar carpetas
```bash
# Crear estructura base
mkdir -p app/api/v1/endpoints
mkdir -p app/api/errors
mkdir -p app/repositories
mkdir -p app/schemas
mkdir -p app/models
mkdir -p tests/{unit,integration,e2e}
mkdir -p examples

# Mover archivos existentes
mv app/core/deps.py app/api/
mv app/routers/{auth,documents,invoices}.py app/api/v1/endpoints/
```

#### 1.3 Crear archivos base
```bash
# Crear __init__.py en todas las nuevas carpetas
touch app/api/__init__.py
touch app/api/errors/__init__.py
touch app/repositories/__init__.py
touch app/schemas/__init__.py
```

### FASE 2: ERROR HANDLING (1-2 días)

#### 2.1 Implementar excepciones personalizadas
📄 Copiar [examples/04_error_handling.py](examples/04_error_handling.py) a:
```
app/api/errors/
├── __init__.py
├── http_errors.py  # Excepciones personalizadas
└── handlers.py     # Exception handlers
```

#### 2.2 Registrar handlers en main.py
```python
# app/main.py

from app.api.errors.handlers import setup_exception_handlers

app = FastAPI(...)
setup_exception_handlers(app)  # ← Agregar esta línea
```

#### 2.3 Actualizar endpoints existentes
```python
# Cambiar en auth.py, documents.py, invoices.py

# De:
raise HTTPException(status_code=404, detail="...")

# A:
from app.api.errors.http_errors import NotFoundException
raise NotFoundException("User", email)
```

### FASE 3: REPOSITORY PATTERN (2-3 días)

#### 3.1 Crear BaseRepository
📄 Copiar [examples/01_base_repository.py](examples/01_base_repository.py) a:
```
app/repositories/base.py
```

#### 3.2 Implementar repositorios específicos
📄 Copiar [examples/02_factura_repository.py](examples/02_factura_repository.py) a:
```
app/repositories/
├── factura_repository.py
├── lote_repository.py
├── user_repository.py
└── __init__.py
```

#### 3.3 Crear dependencia de repositorio
```python
# app/api/deps.py

from app.repositories.factura_repository import FacturaRepository

def get_factura_repository(
    session: AsyncSession = Depends(get_session)
) -> FacturaRepository:
    return FacturaRepository(session)
```

### FASE 4: SERVICE LAYER (3-4 días)

#### 4.1 Crear schemas (DTOs)
📄 Copiar [examples/05_pydantic_schemas.py](examples/05_pydantic_schemas.py) a:
```
app/schemas/
├── __init__.py
├── invoice.py
├── lote.py
├── auth.py
└── common.py
```

#### 4.2 Implementar services
📄 Copiar [examples/03_invoice_service.py](examples/03_invoice_service.py) a:
```
app/services/
├── invoice_service.py  # ← Crear
├── lote_service.py     # ← Crear
├── auth_service.py     # ← Crear
├── transformer.py      # Ya existe
└── api_client.py       # Ya existe
```

#### 4.3 Actualizar endpoints
```python
# app/api/v1/endpoints/invoices.py

from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceCreate, InvoiceResponse

def get_invoice_service(
    factura_repo: FacturaRepository = Depends(get_factura_repository),
    factus_client = Depends(get_factus_client)
) -> InvoiceService:
    return InvoiceService(factura_repo, factus_client)

@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    data: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    return await service.create_invoice(data, current_user.id)
```

### FASE 5: TESTING (3-4 días)

#### 5.1 Configurar pytest
```python
# pytest.ini

[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

#### 5.2 Crear fixtures compartidas
```python
# tests/conftest.py

import pytest
from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
async def db():
    """Database fixture"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # ... crear sesión
    yield session

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)
```

#### 5.3 Escribir tests unitarios
```python
# tests/unit/test_invoice_service.py

import pytest
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceCreate

@pytest.mark.asyncio
async def test_create_invoice_success(invoice_service):
    """Test crear factura válida"""
    data = InvoiceCreate(
        numbering_range_id=1,
        reference_code="TEST-001",
        # ... datos completos
    )
    
    result = await invoice_service.create_invoice(data, user_id=1)
    
    assert result.id is not None
    assert result.estado == "ENVIADA"

@pytest.mark.asyncio
async def test_create_invoice_validation_error(invoice_service):
    """Test crear factura sin items"""
    from app.api.errors.http_errors import ValidationException
    
    data = InvoiceCreate(
        numbering_range_id=1,
        reference_code="TEST-002",
        items=[]  # ← Inválido
    )
    
    with pytest.raises(ValidationException):
        await invoice_service.create_invoice(data, user_id=1)
```

#### 5.4 Tests de integración
```python
# tests/integration/test_api_endpoints.py

@pytest.mark.asyncio
async def test_create_invoice_endpoint(client, authenticated_user):
    """Test endpoint de crear factura"""
    response = client.post(
        "/api/v1/invoices",
        json={
            "numbering_range_id": 1,
            "reference_code": "API-TEST-001",
            # ... datos
        },
        headers={"Authorization": f"Bearer {authenticated_user['token']}"}
    )
    
    assert response.status_code == 201
    assert response.json()["estado"] == "ENVIADA"
```

### FASE 6: CONFIGURACIÓN AVANZADA (2 días)

#### 6.1 Mejorar settings.py
```python
# app/core/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Factus API"
    APP_VERSION: str = "2.0.0"
    APP_MODE: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS384"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Factus API
    FACTUS_URL: str
    FACTUS_TOKEN: str
    FACTUS_TIMEOUT: int = 30
    FACTUS_MOCK_MODE: bool = True  # En TEST
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # segundos
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

#### 6.2 Crear archivos .env por ambiente
```bash
# .env.development
APP_MODE=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://factus_user:factus_password@localhost:5432/factus_db_dev
SECRET_KEY=dev-secret-key-change-in-production
FACTUS_MOCK_MODE=True

# .env.production
APP_MODE=production
DEBUG=False
DATABASE_URL=postgresql+asyncpg://...actual production db
SECRET_KEY=secure-production-key-from-vault
FACTUS_MOCK_MODE=False
FACTUS_URL=https://api.factus.io
FACTUS_TOKEN=<production-token>
```

#### 6.3 Implementar Logging estructurado
```python
# app/core/logging.py

import logging
import json
from datetime import datetime

def setup_logging(app_mode: str, log_level: str):
    """Configurar logging estructurado"""
    
    if app_mode == "production":
        # JSON logging en producción
        logging.config.dictConfig({
            "version": 1,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(timestamp)s %(level)s %(name)s %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "json",
                    "class": "logging.StreamHandler",
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["default"]
            }
        })
    else:
        # Simple logging en desarrollo
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
```

### FASE 7: MIDDLEWARE Y SEGURIDAD (2 días)

#### 7.1 Agregar middleware de logger
```python
# app/main.py

from app.core.middleware import LoggingMiddleware, SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
```

#### 7.2 Implementar rate limiting
```python
# app/core/middleware.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

#### 7.3 CORS y security headers
```python
# app/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### FASE 8: PERFORMANCE (2-3 días)

#### 8.1 Agregar Redis caché
```bash
pip install redis aioredis
```

```python
# app/core/cache.py

import aioredis
from functools import wraps

redis = None

async def init_redis():
    global redis
    redis = await aioredis.from_url("redis://localhost:6379/0")

async def get_cached(key: str):
    return await redis.get(key)

async def set_cached(key: str, value: str, ttl: int = 300):
    await redis.setex(key, ttl, value)
```

#### 8.2 Optimizar queries
```python
# En repositories, usar selectinload para eager loading

from sqlalchemy.orm import selectinload

async def get_lote_with_facturas(self, lote_id: int):
    query = (
        select(Lote)
        .where(Lote.id == lote_id)
        .options(selectinload(Lote.facturas))
    )
    result = await self.session.execute(query)
    return result.scalars().first()
```

### FASE 9: DEPLOYMENT (2-3 días)

#### 9.1 Crear Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 9.2 Docker Compose para producción
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_MODE=production
      - DATABASE_URL=postgresql+asyncpg://...
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: factus_db
      POSTGRES_USER: factus_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    
  celery_worker:
    build: .
    command: celery -A app.core.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres

volumes:
  postgres_data:
```

#### 9.3 CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app
      - run: coverage report --fail-under=80
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: docker build -t factus-api .
      - run: docker push factus-api:latest
      # ... deploy a producción
```

---

## 📊 Checklist de Implementación

### Semana 1: Fundación
- [ ] Fase 1: Setup y carpetas
- [ ] Fase 2: Error handling
- [ ] Fase 3: Repository pattern (50%)

### Semana 2: Servicios
- [ ] Fase 3: Repository pattern (100%)
- [ ] Fase 4: Service layer (50%)
- [ ] Fase 5: Testing setup

### Semana 3: Calidad y Testing
- [ ] Fase 4: Service layer (100%)
- [ ] Fase 5: Testing completo
- [ ] Fase 6: Configuración avanzada

### Semana 4: Optimización y Deployment
- [ ] Fase 7: Middleware y seguridad
- [ ] Fase 8: Performance/Caché
- [ ] Fase 9: Deployment

---

## 🎯 Prioridad: Quick Wins (Haz primero esto)

1. **Error Handling** (1 día)
   - Resultado: Errores claros y consistentes
   - Impacto: Inmediato en debugging

2. **Schemas/DTOs** (1 día)
   - Resultado: Validación automática
   - Impacto: Mejor documentación OpenAPI

3. **BaseRepository** (1 día)
   - Resultado: Menos código duplicado
   - Impacto: Más fácil mantener

4. **Services** (2-3 días) 
   - Resultado: Lógica centralizada
   - Impacto: Escalabilidad

5. **Tests** (3-4 días)
   - Resultado: Confianza en cambios
   - Impacto: Seguridad en refactoring

---

## 📚 Documentación Necesaria

Crear estas docs en `docs/`:
- [ ] API.md - Descripción de endpoints
- [ ] ARCHITECTURE.md - Decisiones de arquitectura
- [ ] DATABASE.md - Schema y relaciones
- [ ] DEPLOYMENT.md - Cómo deployar
- [ ] TESTING.md - Cómo escribir tests
- [ ] CONTRIBUTING.md - Guía para contribuidores

---

## 🔄 proceso de Migración Limpia

```bash
# 1. Crear rama de desarrollo
git checkout -b refactor/architecture

# 2. Implementar cambios fase por fase
# (commit después de cada fase)

# 3. Tests
pytest tests/ --cov=app

# 4. Crear PR para review
# (code review antes de merge)

# 5. Merge a main
git merge --squash refactor/architecture
```

---

## ✅ Validación de Cada Fase

### Fase 1: Setup
```bash
python -c "from app.api.errors import *; print('✓ Errors importan bien')"
python -c "from app.repositories import *; print('✓ Repos importan bien')"
python -c "from app.schemas import *; print('✓ Schemas importan bien')"
```

### Fase 2-5: Endpoints funcionando
```bash
# Test endpoint funciona
curl -X POST http://localhost:8000/api/v1/invoices \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"numbering_range_id": 1, ...}'
```

### Fase 5: Tests pasando
```bash
pytest tests/ --cov=app
# Coverage > 80%
```

### Fase 9: Deploy
```bash
docker-compose -f docker-compose.prod.yml up -d
# Verificar en producción
curl https://api.example.com/health
```

---

¡Empecemos por la Fase 1! ¿Necesitas que te ayude con la implementación específica?
