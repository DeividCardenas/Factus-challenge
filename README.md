# Factus Challenge API (Hybrid REST/GraphQL)

## Descripción
Sistema de facturación de alto rendimiento diseñado para procesar y validar facturas electrónicas. Implementa una arquitectura híbrida que expone tanto una API RESTful como un endpoint GraphQL.

## Stack Tecnológico
- **Lenguaje:** Python 3.11+
- **Framework Web:** FastAPI
- **GraphQL:** Strawberry GraphQL
- **ORM:** SQLModel (Async) con SQLAlchemy
- **Base de Datos:** PostgreSQL (Driver: asyncpg)
- **Procesamiento de Datos:** Polars (para archivos masivos)

## Características Clave
- **Arquitectura de 3 Capas:** Separación clara entre Controladores (API), Servicios (Lógica de Negocio) y Repositorios (Acceso a Datos).
- **Optimización de Rendimiento:** Solución al problema N+1 en GraphQL mediante dataloaders y `selectinload` en SQLAlchemy.
- **Manejo de Errores Centralizado:** Middleware y handlers personalizados para transformar excepciones de negocio en respuestas HTTP/GraphQL estandarizadas.
- **Validación Robusta:** Uso de Pydantic para REST y Inputs tipados para GraphQL.

## Quick Start

### Prerrequisitos
- Python 3.10 o superior
- PostgreSQL corriendo localmente o en Docker

### Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-del-repo>
    cd factus-challenge
    ```

2.  **Crear entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate  # Windows
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar variables de entorno:**
    Crea un archivo `.env` basado en `.env.example` (si existe) o configura la URL de la base de datos:
    ```bash
    export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/factus_db"
    ```

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
