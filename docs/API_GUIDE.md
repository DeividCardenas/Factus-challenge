# Guía de Uso de la API (REST & GraphQL)

A continuación se presentan ejemplos para interactuar con la API mediante `curl` para REST y mediante consultas para el Playground de GraphQL.

## API REST (v1)

Base URL: `http://localhost:8000/api/v1`

### 1. Iniciar Sesión (Obtener Token)

Para acceder a los endpoints protegidos, primero debes autenticarte.

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@factus.co&password=secretpassword"
```

**Respuesta Exitosa (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Crear una Factura Individual

Una vez tengas el token, úsalo en el header `Authorization`.

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/facturas" \
     -H "Authorization: Bearer <TU_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "numbering_range_id": 8,
       "reference_code": "FAC-001",
       "observation": "Venta de Servicios",
       "payment_form": "CASH",
       "payment_method_code": "10",
       "customer": {
         "identification": "123456789",
         "dv": "3",
         "company": "Cliente Prueba S.A.S",
         "trade_name": "Cliente Prueba",
         "names": "Juan Perez",
         "address": "Calle 123 # 45-67",
         "email": "cliente@prueba.com",
         "phone": "3001234567",
         "legal_organization_id": "2",
         "tribute_id": "21",
         "identification_document_id": "3",
         "municipality_id": "980"
       },
       "items": [
         {
           "code_reference": "ITEM-001",
           "name": "Consultoria TI",
           "quantity": 1,
           "discount_rate": 0,
           "price": 150000,
           "tax_rate": 19.00,
           "unit_measure_id": "70",
           "standard_code_id": "1",
           "is_excluded": 0,
           "tribute_id": "1",
           "withholding_taxes": []
         }
       ]
     }'
```

---

## API GraphQL

Endpoint: `http://localhost:8000/graphql`

### 1. Obtener Dashboard (Resumen de Lotes)

Consulta para obtener estadísticas de lotes procesados y sus facturas asociadas.

**Query:**

```graphql
query GetDashboard {
  lotes {
    id
    nombreArchivo
    fechaCarga
    estado
    totalRegistros
    totalErrores
    facturas {
      id
      referenceCode
      estado
      total
    }
  }
}
```

### 2. Crear un Lote (Simulación)

Mutation para crear un nuevo registro de lote (nota: en la práctica, esto suele dispararse al subir un archivo, pero aquí se muestra como mutación directa si estuviera expuesta).

**Mutation:**

```graphql
mutation CreateLoteExample {
  crearLote(input: {
    nombreArchivo: "facturas_agosto.xlsx",
    fechaCarga: "2023-08-01T10:00:00"
  }) {
    lote {
      id
      estado
      nombreArchivo
    }
    success
    errors
  }
}
```

**Respuesta Exitosa:**

```json
{
  "data": {
    "crearLote": {
      "lote": {
        "id": "1",
        "estado": "PROCESADO",
        "nombreArchivo": "facturas_agosto.xlsx"
      },
      "success": true,
      "errors": null
    }
  }
}
```
