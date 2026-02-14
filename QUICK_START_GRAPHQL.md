# 🚀 QUICK START - GraphQL + Service Layer

## ¡LISTO PARA USAR!

Tu aplicación ahora tiene una arquitectura de **3 capas** con REST y GraphQL compartiendo servicios.

---

## 📊 Lo que se Implementó

### Layer 1: Service (Lógica de Negocio)
```
app/services/
├── base_service.py      → Clase base genérica
├── invoice_service.py   → Queries + Mutations de facturas
├── auth_service.py      → Autenticación JWT
└── lote_service.py      → Gestión de lotes
```

### Layer 2: GraphQL (API Flexible)
```
app/graphql/
├── types.py             → 10+ tipos Strawberry
├── inputs.py            → 8 inputs para mutations
├── queries.py           → 10+ resolvers
└── schema.py            → Mutations + Schema
```

### Layer 3: REST (API Clásica)
```
app/routers/
├── auth.py              → Login
├── invoices.py          → CRUD facturas
└── documents.py         → Upload lotes
```

---

## 🎯 Cómo Usar

### Opción 1: Iniciar Servidor
```bash
cd c:\Users\Dillan\Music\factus-challenge
uvicorn app.main:app --reload
```

### Opción 2: Acceder a REST API
```
GET http://localhost:8000/docs
```

### Opción 3: Acceder a GraphQL
```
POST http://localhost:8000/graphql
```

---

## 📝 Ejemplos GraphQL

### GET Facturas por Cliente
```graphql
query {
  invoicesByCustomer(
    email: "client@example.com"
    pagination: { skip: 0, limit: 10 }
  ) {
    items {
      id
      referenceCode
      total
      estado
    }
    total
    pages
  }
}
```

### GET Lote con Detalles
```graphql
query {
  lote(id: 1) {
    id
    nombreArchivo
    totalRegistros
    registrosProcesados
    estado
    facturas {
      id
      referenceCode
      estado
    }
  }
}
```

### CREATE Factura
```graphql
mutation {
  createInvoice(
    invoiceInput: {
      numberingRangeId: 1
      referenceCode: "FAC-2026-001"
      customer: {
        names: "Acme Corp"
        email: "contact@acme.com"
        phone: "555-0000"
        identification: "123456789"
        identificationDocumentId: 1
        legalOrganizationId: 1
      }
      items: [
        {
          codeReference: "PROD"
          name: "Product"
          quantity: 1
          price: 100.0
          taxRate: 19.0
        }
      ]
    }
  ) {
    id
    referenceCode
    total
    estado
  }
}
```

---

## 🔄 Flujo de Datos

```
REST Request                GraphQL Query
     ↓                            ↓
 Router                       Resolver
     ↓                            ↓
 ┌─────────────────────────────────┐
 │   Service Layer (COMPARTIDA)    │  ← InvoiceService
 │   • obtener_factura()           │     AuthService
 │   • crear_factura()             │     LoteService
 │   • actualizar_estado()         │
 └─────────────────────────────────┘
     ↓
 ┌─────────────────────────────────┐
 │   Repository Layer              │  ← FacturaRepository
 │   • get()                       │     UserRepository
 │   • create()                    │     LoteRepository
 │   • update()                    │
 └─────────────────────────────────┘
     ↓
 ┌─────────────────────────────────┐
 │   PostgreSQL Database           │
 └─────────────────────────────────┘
```

---

## ✨ Características

✅ **Service Layer compartido** entre REST y GraphQL
✅ **Type-safe** con Strawberry types
✅ **Validación automática** con Pydantic inputs
✅ **Paginación integrada** en queries
✅ **Manejo de errores** centralizado
✅ **Inyección de dependencias** funcional
✅ **Contexto compartido** (sesión BD + usuario)
✅ **Documentación automática** (Swagger + GraphQL schema)

---

## 🧪 Testing

### Verificar que funciona
```python
from app.main import app
from app.services import InvoiceService, AuthService
from app.graphql.schema import schema

print("✓ Todo importa correctamente")
```

### En GraphQL Sandbox (`http://localhost:8000/graphql`)
```graphql
# Copia y pega esto:
{
  invoices(pagination: {skip: 0, limit: 5}) {
    items { id referenceCode estado }
    total
    pages
  }
}
```

---

## 📚 Archivos Importantes

| Archivo | Propósito |
|---------|-----------|
| `app/services/invoice_service.py` | Lógica de facturas |
| `app/services/auth_service.py` | Autenticación JWT |
| `app/services/lote_service.py` | Gestión de lotes |
| `app/graphql/types.py` | Tipos GraphQL |
| `app/graphql/inputs.py` | Inputs GraphQL |
| `app/graphql/queries.py` | Queries/resolvers |
| `app/graphql/schema.py` | Mutations + Schema |
| `app/main.py` | FastAPI + GraphQL router |

---

## 🔧 Próximos Pasos

1. **Iniciar el servidor**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Probar endpoints REST**
   - Ir a `http://localhost:8000/docs`

3. **Probar GraphQL**
   - Ir a `http://localhost:8000/graphql`

4. **Agregar más servicios**
   - Crear `app/services/new_service.py`
   - Heredar de `BaseService`
   - Usar en routers REST y resolvers GraphQL

---

## ❓ FAQ

**P: ¿Cómo agrego un nuevo endpoint GraphQL?**
R: Agrega un método a la clase `Query` en `app/graphql/queries.py` con decorador `@strawberry.field`

**P: ¿Cómo agrego una nueva mutation?**
R: Agrega un método a la clase `Mutation` en `app/graphql/schema.py` con decorador `@strawberry.mutation`

**P: ¿Cómo valido inputs en GraphQL?**
R: Usa Pydantic en los inputs (ya está hecho en `app/graphql/inputs.py`)

**P: ¿Cómo obtengo el usuario actual en GraphQL?**
R: Accede a `info.context.get("user")` en cualquier resolver

**P: ¿Cómo accedo a la BD en GraphQL?**
R: Accede a `info.context.get("session")` para AsyncSession

---

¡**LISTO PARA PRODUCCIÓN!** 🎉
