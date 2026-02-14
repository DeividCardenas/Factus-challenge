# Factus Challenge API - Architectura Profesional

## 📋 Descripción

Sistema de facturación de alto rendimiento con arquitectura profesional de 3 capas:
- **API híbrida**: REST + GraphQL en un mismo servidor
- **Services Layer**: Lógica de negocio centralizada
- **Repository Pattern**: Acceso a datos reutilizable
- **Async/Await**: 100% operaciones no bloqueantes
- **PostgreSQL**: Base de datos robusta con asyncpg

## 🏗️ Arquitectura

```
┌─────────────────────────┐
│     REST + GraphQL      │
│     (FastAPI)           │
├─────────────────────────┤
│    Service Layer        │
│    (Lógica Negocio)     │
├─────────────────────────┤
│ Repository Layer/CRUD   │
│ (Acceso a Datos)        │
├─────────────────────────┤
│  PostgreSQL + Asyncpg   │
└─────────────────────────┘
```

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| **Backend** | Python 3.11+ FastAPI |
| **GraphQL** | Strawberry GraphQL |
| **ORM** | SQLModel (async) |
| **BD** | PostgreSQL + asyncpg |
| **Procesamiento** | Polars |
| **Validación** | Pydantic |
| **Task Queue** | Celery (redis) |

## ⚡ Características

✅ **Clean Architecture** - Separación clara de responsabilidades  
✅ **Async/Await** - 100% no bloqueante  
✅ **GraphQL** - Queries flexibles + REST en mismo servidor  
✅ **Error Handling** - Excepciones personalizadas estandarizadas  
✅ **Type Safety** - tipos genéricos y Pydantic  
✅ **Dev/Prod Config** - Múltiples ambientes soportados  
✅ **Dependency Injection** - Services inyectados en endpoints  

## 🚀 Quick Start

### 1. Clonar y Setup

```bash
# Clonar
git clone <repo-url>
cd factus-challenge

# Entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

```bash
# Opción A: PostgreSQL local
createdb factus_db
# Crear usuario:
psql -U postgres
CREATE USER factus_user WITH PASSWORD 'factus_password';
ALTER ROLE factus_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE factus_db TO factus_user;

# Opción B: Docker Compose
docker-compose up -d postgres redis
```

### 3. Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env con tus valores
APP_MODE=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://factus_user:factus_password@localhost:5432/factus_db
SECRET_KEY=your-secret-key-here
FACTUS_MOCK_MODE=True
```

### 4. Crear Tablas

```bash
# Crear tablas automáticamente (en app/core/database.py)
python
>>> from app.core.database import init_db
>>> import asyncio
>>> asyncio.run(init_db())
```

### 5. Iniciar Servidor

```bash
uvicorn app.main:app --reload

# El servidor estará en:
# - API Docs: http://localhost:8000/docs
# - GraphQL: http://localhost:8000/graphql
# - Healthcheck: http://localhost:8000/health
```

## 📚 Documentación

### Arquitectura & Mejores Prácticas
📖 [ARQUITECTURA_IMPLEMENTADA.md](docs/ARQUITECTURA_IMPLEMENTADA.md) - Guía completa de arquitectura y patrones

### Validación del Sistema
✅ [VALIDACION_ARQUITECTURA.md](docs/VALIDACION_ARQUITECTURA.md) - Checklist de validación

### API Endpoints

#### REST API

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password"}'

# Crear factura
curl -X POST http://localhost:8000/api/v1/facturas \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "numbering_range_id": 1,
    "reference_code": "FAC-001",
    "customer": {...},
    "items": [...]
  }'

# Listar facturas
curl -X GET http://localhost:8000/api/v1/facturas?skip=0&limit=10 \
  -H "Authorization: Bearer <token>"
```

#### GraphQL API

Ir a `http://localhost:8000/graphql` y ejecutar queries:

```graphql
# Obtener factura
query {
  invoice(id: 1) {
    id
    reference_code
    cliente_email
    total
    estado
  }
}

# Listar facturas
query {
  invoices(
    estado: "ENVIADA"
    pagination: {skip: 0, limit: 10}
  ) {
    items {
      id
      reference_code
      total
    }
    total
    pages
  }
}

# Crear factura
mutation {
  createInvoice(
    invoiceInput: {
      numbering_range_id: 1
      reference_code: "FAC-002"
      customer: {...}
      items: [...]
    }
  ) {
    id
    reference_code
    estado
  }
}
```

## 🏃 Estructura de Carpetas

```
factus-challenge/
│
├── app/
│   ├── api/                      # Capa de presentación
│   │   ├── v1/
│   │   │   ├── endpoints/        # Routers REST
│   │   │   └── service_deps.py   # Inyección de servicios
│   │   └── errors/               # Manejo de errores
│   │
│   ├── services/                 # Lógica de negocio
│   │   ├── base_service.py       # Clase base reutilizable
│   │   ├── invoice_service.py    # Facturas
│   │   ├── auth_service.py       # Autenticación
│   │   └── lote_service.py       # Lotes
│   │
│   ├── repositories/             # Acceso a datos
│   │   ├── base.py               # CRUD genérico
│   │   ├── factura_repository.py
│   │   ├── user_repository.py
│   │   └── lote_repository.py
│   │
│   ├── graphql/                  # GraphQL resolvers
│   │   ├── types.py              # Tipos Strawberry
│   │   ├── inputs.py             # Inputs
│   │   ├── queries.py            # Queries
│   │   └── schema.py             # Schema + Mutations
│   │
│   ├── models/                   # SQLModel ORM models
│   ├── schemas/                  # Pydantic DTOs
│   ├── core/                     # Configuración
│   │   ├── config.py             # Settings (dev/prod)
│   │   ├── database.py
│   │   ├── deps.py
│   │   └── security.py
│   │
│   └── main.py                   # FastAPI app
│
├── tests/
│   ├── unit/                     # Tests unitarios
│   ├── integration/              # Tests de integración
│   └── e2e/                      # Tests end-to-end
│
├── docs/
│   ├── ARQUITECTURA_IMPLEMENTADA.md
│   └── VALIDACION_ARQUITECTURA.md
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── alembic/                      # Migraciones BD
```

## 🔧 Configuración

### Variables de Entorno

Ver `.env.example` para todas las opciones:

```bash
# Modo
APP_MODE=development|staging|production

# Servidor
HOST=127.0.0.1
PORT=8000

# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Seguridad
SECRET_KEY=your-secret-key
ALGORITHM=HS384

# API externa
FACTUS_MOCK_MODE=True|False

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json|text
```

### Desarrollo vs Producción

El proyecto detecta automáticamente el modo:

**Desarrollo** (.env):
```
APP_MODE=development
DEBUG=True
FACTUS_MOCK_MODE=True
LOG_FORMAT=text
```

**Producción** (.env):
```
APP_MODE=production
DEBUG=False
FACTUS_MOCK_MODE=False
LOG_FORMAT=json
SECRET_KEY=<secure-key>
DATABASE_URL=<prod-db>
```

## 💡 Cómo Usar

### Patrón de Uso - REST

```python
from app.api.v1.service_deps import get_invoice_service
from app.services.invoice_service import InvoiceService
from app.models import User

@router.post("/facturas")
async def crear_factura(
    factura_in: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    service: InvoiceService = Depends(get_invoice_service)  # ✅ Inyectado
):
    # Service se inyecta automáticamente
    return await service.crear_factura(factura_in, current_user.id)
```

### Patrón de Uso - GraphQL

```python
@strawberry.field
async def invoice(self, info: Info, id: int) -> InvoiceType:
    session = info.context.get("session")  # ✅ Contexto
    service = InvoiceService(session)
    result = await service.obtener_factura(id)  # ✅ Await (async)
    return InvoiceType.from_orm(result)
```

### Métodos Disponibles

#### Service Methods

```python
# Lectura
factura = await service.get(id=1)
facturas = await service.get_all(skip=0, limit=100)
total = await service.count()
existe = await service.exists(id=1)

# Escritura
created = await service.create(obj)
updated = await service.update(obj)
deleted = await service.delete(id=1)

# Paginación
result = await service.get_paginated(skip=0, limit=10, estado="ENVIADA")
```

#### Repository Methods

```python
# BASE REPOSITORY
repo = FacturaRepository(session)

# Búsqueda especializada
factura = await repo.get_by_reference_code("FAC-001")
facturas = await repo.get_by_lote(lote_id=1, estado="ENVIADA")
facturas = await repo.get_by_cliente_email("cliente@example.com")

# Estadísticas
stats = await repo.get_estadisticas_lote(lote_id=1)

# Bulk operations
created = await repo.bulk_create([factura1, factura2])
```

## 🧪 Testing

### Estructura

```
tests/
├── conftest.py           # Fixtures compartidas
├── unit/                 # Tests unitarios (servicios, repos)
├── integration/          # Tests de endpoints y graphql
└── e2e/                  # Tests end-to-end completos
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=app tests/

# Solo unitarios
pytest tests/unit/

# Con verbose
pytest -v
```

## 📈 Performance

- ✅ **Async/Await** - Sin threads bloqueantes
- ✅ **Connection Pooling** - Pool de conexiones a BD
- ✅ **Query Optimization** - selectinload para N+1
- ⏳ **Caché Redis** - Implementar para estadísticas
- ⏳ **Rate Limiting** - Limitar requests por IP

## 🚀 Deployment

### Docker

```bash
# Build
docker build -t factus-api .

# Run
docker run -p 8000:8000 -e DATABASE_URL="..." factus-api

# Con Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Ready

El proyecto está preparado para Kubernetes con:
- ✅ Health checks (`/health`)
- ✅ Graceful shutdown
- ✅ Configuración por variables de entorno
- ✅ Logging estructurado

## 📝 Próximas Mejoras

- [ ] Tests unitarios completos
- [ ] Tests de integración
- [ ] Rate limiting con slowapi
- [ ] Caché Redis
- [ ] Monitoring con Prometheus
- [ ] Documentación OpenAPI mejorada
- [ ] CI/CD pipeline (GitHub Actions)

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama: `git checkout -b feature/nueva-feature`
3. Commit: `git commit -am 'Agregar feature'`
4. Push: `git push origin feature/nueva-feature`
5. Pull Request

## 📄 Licencia

Este proyecto es privado. Todos los derechos reservados.

## 👨‍💻 Autor

**Dillan Cardenas** - [DeividCardenas](https://github.com/DeividCardenas)

---

## 📞 Support

Para preguntas o issues:
1. Revisar [ARQUITECTURA_IMPLEMENTADA.md](docs/ARQUITECTURA_IMPLEMENTADA.md)
2. Revisar [VALIDACION_ARQUITECTURA.md](docs/VALIDACION_ARQUITECTURA.md)
3. Abrir issue en GitHub

---

**¡Proyecto listo para producción!** 🚀

### Ejecución

Levantar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload
```

El servidor iniciará en `http://localhost:8000`.

## Documentación y Enlaces

- **REST API Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **GraphQL Playground:** [http://localhost:8000/graphql](http://localhost:8000/graphql)
- **Documentación de Arquitectura:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Guía de Uso de la API:** [docs/API_GUIDE.md](docs/API_GUIDE.md)
