"""
Exception handlers para centralizar el manejo de errores.
Proporciona respuestas estandarizadas para todos los tipos de excepciones.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .http_errors import APIException
from app.core.config import settings


def create_error_response(
    status_code: int,
    error_code: str,
    detail: str,
    extra: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Crear respuesta de error estandarizada"""
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": detail,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }

    if extra:
        response["error"]["details"] = extra

    if request_id:
        response["request_id"] = request_id

    return response


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handler para excepciones personalizadas de API"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            detail=exc.detail,
            extra=exc.extra,
            request_id=request.headers.get("X-Request-ID"),
        ),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handler para excepciones HTTP de Starlette"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            detail=exc.detail,
            request_id=request.headers.get("X-Request-ID"),
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handler para errores de validación de Pydantic"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"][1:])
        errors.append(
            {"field": field, "message": error["msg"], "type": error["type"]}
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            detail="Request validation failed",
            extra={"errors": errors},
            request_id=request.headers.get("X-Request-ID"),
        ),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para excepciones no manejadas (500)"""
    import traceback

    error_trace = traceback.format_exc()
    print(f"Unhandled exception: {error_trace}")

    # En producción, no exponer detalles internos
    detail = str(exc) if settings.DEBUG else "Internal server error"
    extra = {"trace": error_trace} if settings.DEBUG else None

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            detail=detail,
            extra=extra,
            request_id=request.headers.get("X-Request-ID"),
        ),
    )


def setup_exception_handlers(app: FastAPI):
    """Registrar todos los exception handlers en la app"""

    # Handlers personalizados
    app.add_exception_handler(APIException, api_exception_handler)

    # Handlers de FastAPI/Starlette
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Handler catch-all para errores no manejados
    app.add_exception_handler(Exception, general_exception_handler)
