# 📐 GUÍA DE ARQUITECTURA Y MEJOR PRÁCTICAS

## 1. ESTRUCTURA DE CAPAS

Tu proyecto implementa **Clean Architecture** con 4 capas claramente separadas:

```
┌─────────────────────────────────────────┐
│         API LAYER (Endpoints)           │
│  ├─ app/routers/                        │
│  └─ app/api/v1/endpoints/               │
│  ├─ GraphQL Resolvers (app/graphql/)    │
└──────────────┬──────────────────────────┘
               ↓ Depends()
┌─────────────────────────────────────────┐
│      SERVICE LAYER (Lógica Negocio)     │
│  ├─ app/services/invoice_service.py     │
│  ├─ app/services/auth_service.py        │
│  ├─ app/services/lote_service.py        │
│  └─ app/services/base_service.py        │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   REPOSITORY LAYER (Acceso a Datos)     │
│  ├─ app/repositories/base.py            │
│  ├─ app/repositories/factura_repo.py    │
│  ├─ app/repositories/user_repo.py       │
│  └─ app/repositories/lote_repo.py       │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      DATABASE LAYER (PostgreSQL)        │
│  ├─ app/models/ (SQLModel ORM)          │
│  └─ app/core/database.py                │
└─────────────────────────────────────────┘
```

---

## 2. FLUJO DE REQUEST - EJEMPLO COMPLETO

### Crear Factura vía REST API

```python
# 1️⃣ REQUEST LLEGA A ENDPOINT
@router.post("/facturas", response_model=InvoiceResponse)
async def crear_factura_individual(
    factura_in: InvoiceCreate,  # ← Pydantic valida automáticamente
    current_user: User = Depends(get_current_user),  # ← Inyección auth
    session: AsyncSession = Depends(get_session)  # ← Inyección BD
):
    # 2️⃣ INYECTAR SERVICE
    service = InvoiceService(session)
    
    # 3️⃣ INVOCAR MÉTODO DE SERVICIO
    return await service.crear_factura(factura_in, current_user.id)

# SERVICE LAYER (invoice_service.py)
class InvoiceService(BaseService[Factura, InvoiceResponse]):
    async def crear_factura(self, factura_in, usuario_id):
        # Validación de negocio
        existing = await self.repo.get_by_reference_code(ref)
        if existing:
            raise ConflictException(...)
        
        # Crear modelo ORM
        factura = Factura(...)
        
        # 4️⃣ INVOCAR REPOSITORY
        created = await self.repo.create(factura)
        
        # 5️⃣ RETORNAR DTO
        return InvoiceResponse.from_orm(created)

# REPOSITORY LAYER (factura_repository.py)
class FacturaRepository(BaseRepository[Factura]):
    async def create(self, obj):
        # 6️⃣ GUARDAR EN BD
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
```

**Flujo Completo:**
```
Request → Endpoint (valida) → Service (lógica) → Repository (BD) → Response
```

---

## 3. INYECCIÓN DE DEPENDENCIAS

### ✅ FORMA CORRECTA (Usar Depends)

```python
# En endpoints - Los servicios se crean automáticamente
from app.api.v1.service_deps import get_invoice_service

@router.get("/facturas/{id}")
async def get_invoice(
    id: int,
    service: InvoiceService = Depends(get_invoice_service)  # ← Inyectado
):
    return await service.obtener_factura(id)

# En app/api/v1/service_deps.py
async def get_invoice_service(
    session: AsyncSession = Depends(get_session)
) -> InvoiceService:
    return InvoiceService(session)
```

### ❌ FORMA INCORRECTA (Evitar)

```python
# MAL - Crear servicio directamente
@router.get("/facturas/{id}")
async def get_invoice(id: int, session = Depends(get_session)):
    service = InvoiceService(session)  # ← No usar así
    return await service.obtener_factura(id)

# Problemas:
# - Difícil de testear (no puedes mockear fácilmente)
# - Responsabilidades mixtas en endpoint
# - No reutilizable
```

---

## 4. CÓMO USAR LOS SERVICIOS

### BaseService (Métodos Base)

Todos los servicios heredan de BaseService y tienen estos métodos disponibles:

```python
# Inicializar
service = InvoiceService(session)

# ========= LECTURA ==========

# Obtener uno
factura = await service.get(id=1)

# Obtener todos con paginación
facturas = await service.get_all(skip=0, limit=100)

# Obtener con filtros
facturas = await service.get_all(
    skip=0, 
    limit=100,
    estado="ENVIADA",  # ← Filtro dinámico
    lote_id=5
)

# Contar
total = await service.count()
total_enviadas = await service.count(estado="ENVIADA")

# Verificar existencia
existe = await service.exists(id=1)

# Obtener paginado con metadata
result = await service.get_paginated(
    skip=0,
    limit=10,
    estado="ENVIADA"
)
# Retorna:
# {
#     'items': [...],
#     'total': 100,
#     'skip': 0,
#     'limit': 10,
#     'pages': 10,
#     'current_page': 1
# }

# ========= ESCRITURA ==========

# Crear uno
factura = Factura(...)
created = await service.create(factura)

# Crear múltiples
facturas = [Factura(...), Factura(...)]
results = await service.bulk_create(facturas)

# Actualizar
factura.estado = "ENVIADA"
updated = await service.update(factura)

# Eliminar
deleted = await service.delete(id=1)
```

### InvoiceService (Métodos Especializados)

```python
service = InvoiceService(session)

# Obtener factura
factura = await service.obtener_factura(id=1)

# Obtener Por cliente
facturas = await service.obtener_facturas_cliente(
    email="cliente@example.com",
    skip=0,
    limit=50
)

# Obtener por lote
facturas = await service.obtener_facturas_lote(
    lote_id=1,
    estado="ENVIADA",
    skip=0,
    limit=50
)

# Estadísticas
stats = await service.obtener_estadisticas_lote(lote_id=1)
# Retorna: {total, enviadas, rechazadas, pendientes, ...}

# Listar con filtros
facturas = await service.listar_facturas(
    estado="ENVIADA",
    skip=0,
    limit=100
)

# Crear factura
factura = await service.crear_factura(
    factura_in=InvoiceCreate(...),
    usuario_id=1
)

# Actualizar estado
factura = await service.actualizar_estado_factura(
    factura_id=1,
    nuevo_estado="ENVIADA",
    motivo=None
)

# Crear en lote
result = await service.bulk_crear_facturas(
    facturas_in=[InvoiceCreate(...), ...],
    usuario_id=1
)
```

---

## 5. REPOSITORYS - ACCESO A DATOS

### BaseRepository (Métodos Base)

```python
repo = FacturaRepository(session)

# ========= LECTURA ==========
factura = await repo.get(id=1)
facturas = await repo.get_all(skip=0, limit=100)
total = await repo.count()
existe = await repo.exists(id=1)

# ========= ESCRITURA ==========
factura = Factura(...)
created = await repo.create(factura)
updated = await repo.update(factura)
deleted = await repo.delete(id=1)
```

### FacturaRepository (Métodos Especializados)

```python
repo = FacturaRepository(session)

# Búsqueda por referencia
factura = await repo.get_by_reference_code(ref_code="FACT-001")

# Facturas de un lote
facturas = await repo.get_by_lote(lote_id=1, estado="ENVIADA")

# Facturas de un cliente
facturas = await repo.get_by_cliente_email(
    email="cliente@example.com",
    skip=0,
    limit=50
)

# Estadísticas agregadas
stats = await repo.get_estadisticas_lote(lote_id=1)

# Crear múltiples en transacción
facturas = await repo.bulk_create([...])

# Actualizar estado
factura = await repo.update_estado(
    factura_id=1,
    nuevo_estado="ENVIADA",
    motivo=None,
    api_response={...}
)
```

### UserRepository

```python
repo = UserRepository(session)

# Búsqueda por email
user = await repo.get_by_email(email="user@example.com")

# Verificar si existe
exists = await repo.email_exists(email="user@example.com")
```

### LoteRepository

```python
repo = LoteRepository(session)

# (Métodos similares a otros repos)
```

---

## 6. TIPOS DE DATOS - SCHEMAS

### DTOs de Entrada (Validación)

```python
# app/schemas/invoice.py

class ItemCreate(BaseModel):
    """Un item de factura"""
    code_reference: str
    name: str
    quantity: int = Field(..., gt=0)  # > 0
    price: float = Field(..., ge=0)   # >= 0
    tax_rate: float = Field(..., ge=0, le=100)
    discount_rate: float = Field(..., ge=0, le=100)

class CustomerCreate(BaseModel):
    """Datos del cliente"""
    names: str
    email: EmailStr  # ← Validación de email automática
    phone: str
    identification: str
    identification_document_id: int
    legal_organization_id: int

class InvoiceCreate(BaseModel):
    """Para crear una factura"""
    numbering_range_id: int = Field(..., gt=0)
    reference_code: str = Field(..., min_length=1)
    customer: CustomerCreate
    items: List[ItemCreate] = Field(..., min_items=1)
    
    @validator("items")
    def validate_items(cls, items):
        if not items:
            raise ValueError("At least one item required")
        return items
```

### DTOs de Salida (Serialización)

```python
class InvoiceResponse(BaseModel):
    """Respuesta de factura"""
    id: int
    reference_code: str
    cliente_email: str
    total: float
    estado: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Permite .from_orm()
```

---

## 7. MANEJO DE ERRORES

### Excepciones Personalizadas

```python
from app.api.errors.http_errors import (
    NotFoundException,
    ValidationException,
    ConflictException,
    UnauthorizedException
)

# Uso en servicios
if not factura:
    raise NotFoundException("Factura", factura_id)

if existing:
    raise ConflictException("Reference code already exists")

if errors:
    raise ValidationException(errors)
```

### Formato de Respuesta Estandarizado

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Factura with id '123' not found",
    "status_code": 404,
    "timestamp": "2026-02-14T10:30:45",
    "details": {
      "resource": "Factura",
      "identifier": "123"
    }
  }
}
```

---

## 8. GRAPHQL - RESOLVERS ASYNC

### ✅ CORRECTO - Usar async/await

```python
@strawberry.field
async def invoice(self, info: Info, id: int) -> InvoiceType:
    """Query async correcta"""
    session = info.context.get("session")
    service = InvoiceService(session)
    
    # ← Await es necesario para operaciones async
    invoice_response = await service.obtener_factura(id)
    
    return InvoiceType(
        id=invoice_response.id,
        # ... campos
    )

@strawberry.mutation
async def create_invoice(
    self, info: Info, invoice_input: InvoiceCreateInput
) -> InvoiceType:
    """Mutation async correcta"""
    session = info.context.get("session")
    service = InvoiceService(session)
    
    # ← Await aquí es crítico
    created = await service.crear_factura(...)
    
    return InvoiceType(...)
```

### Contexto en GraphQL

```python
# En main.py
async def get_graphql_context(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Proporciona contexto para resolvers"""
    return {
        "session": db,  # ← Para acceder en resolvers
        "user": user,   # ← Usuario actual si autenticado
        "request": request
    }

# En resolver
async def invoice(self, info: Info, id: int):
    session = info.context.get("session")  # ← Acceso a contexto
    service = InvoiceService(session)
    return await service.obtener_factura(id)
```

---

## 9. VARIAVLES DE ENTORNO - Dev vs Prod

### .env (Desarrollo)
```
APP_MODE=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://...localhost...
FACTUS_MOCK_MODE=True
LOG_FORMAT=text
```

### .env (Producción)
```
APP_MODE=production
DEBUG=False
DATABASE_URL=postgresql+asyncpg://...production...
SECRET_KEY=<secure-production-key>
FACTUS_MOCK_MODE=False
FACTUS_URL=https://api.factus.io
FACTUS_TOKEN=<production-token>
LOG_FORMAT=json
```

### Acceder en Code

```python
from app.core.config import settings

if settings.APP_MODE == "production":
    # Hacer algo solo en prod
    pass

if settings.DEBUG:
    # Solo en desarrollo
    pass

# Base de datos
database_url = settings.DATABASE_URL

# Factus API
if settings.FACTUS_MOCK_MODE:
    # Usar mock
else:
    # Llamar API real
```

---

## 10. CHECKLIST - PASOS PARA AGREGAR UNA NUEVA FEATURE

### 1. Crear DTO (Schema)
```python
# app/schemas/new_feature.py
class NewFeatureCreate(BaseModel):
    field1: str
    field2: int
```

### 2. Crear Service
```python
# app/services/new_feature_service.py
class NewFeatureService(BaseService[Model, Response]):
    async def crear(...):
        # Lógica de negocio
```

### 3. Crear Repository (si accede a BD)
```python
# app/repositories/new_feature_repo.py
class NewFeatureRepository(BaseRepository[Model]):
    async def get_by_custom(...):
        # Query SQL
```

### 4. Crear Endpoint REST
```python
# app/routers/new_feature.py
@router.post("/new-features")
async def create_new_feature(
    data: NewFeatureCreate,
    service: NewFeatureService = Depends(get_service)
):
    return await service.crear(data)
```

### 5. Crear Query GraphQL
```python
# app/graphql/queries.py
@strawberry.field
async def new_feature(self, info: Info, id: int):
    session = info.context.get("session")
    service = NewFeatureService(session)
    return await service.obtener(id)
```

### 6. Crear Tests
```python
# tests/unit/test_new_feature_service.py
async def test_crear_new_feature():
    # Test de lógica de negocio
```

---

## 11. TESTING - UNITTEST EXAMPLE

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_create_invoice_success():
    # 1. Arrange - Preparar
    session = AsyncMock()
    repo = Mock()
    repo.get_by_reference_code = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=Mock(...))
    
    service = InvoiceService(session)
    service.repo = repo
    
    # 2. Act - Ejecutar
    result = await service.crear_factura(
        InvoiceCreate(...),
        usuario_id=1
    )
    
    # 3. Assert - Verificar
    assert result.id is not None
    repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_invoice_duplicate_reference():
    # Verificar que lanza excepción si referencia existe
    session = AsyncMock()
    repo = Mock()
    repo.get_by_reference_code = AsyncMock(
        return_value=Mock(id=1)  # Ya existe
    )
    
    service = InvoiceService(session)
    service.repo = repo
    
    with pytest.raises(ConflictException):
        await service.crear_factura(
            InvoiceCreate(reference_code="DUP"),
            usuario_id=1
        )
```

---

## 📚 Resumen de Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `app/core/config.py` | Configuración centralizada |
| `app/services/base_service.py` | Clase base para servicios |
| `app/repositories/base.py` | CRUD genérico |
| `app/api/v1/service_deps.py` | Inyección de servicios |
| `app/graphql/queries.py` | GraphQL resolvers (async) |
| `app/routers/` | REST endpoints |

---

## 🎯 Próximas Mejoras Sugeridas

1. ✅ **Validación de GraphQL Async** - YA IMPLEMENTADO
2. ✅ **Configuración Dev/Prod** - YA IMPLEMENTADO
3. ✅ **BaseService Completo** - YA IMPLEMENTADO
4. ⏳ **Crear Tests Unitarios** - TODO
5. ⏳ **Agregar Rate Limiting** - TODO
6. ⏳ **Implementar Caché Redis** - TODO
7. ⏳ **Logging Estructurado** - TODO

---

¡Tu arquitectura ya está lista para producción! 🚀
