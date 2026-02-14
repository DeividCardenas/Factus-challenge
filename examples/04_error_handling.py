# Custom Exceptions y Error Handling Centralizado

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from datetime import datetime

# ============= EXCEPCIONES PERSONALIZADAS =============

class APIException(Exception):
    """Excepción base para todas las excepciones de la API"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.extra = extra or {}
        super().__init__(detail)


class NotFoundException(APIException):
    """Recurso no encontrado (404)"""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found",
            error_code="NOT_FOUND",
            extra={"resource": resource, "identifier": str(identifier)}
        )


class ValidationException(APIException):
    """Error de validación de negocio (422)"""
    
    def __init__(self, errors: List[str]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation failed",
            error_code="VALIDATION_ERROR",
            extra={"errors": errors}
        )


class UnauthorizedException(APIException):
    """No autenticado (401)"""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


class ForbiddenException(APIException):
    """Sin permisos (403)"""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class ConflictException(APIException):
    """Conflicto de recursos (409)"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT"
        )


class ExternalServiceException(APIException):
    """Error en servicio externo (502)"""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External service '{service}' failed: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            extra={"service": service, "message": message}
        )


class RateLimitException(APIException):
    """Límite de tasa excedido (429)"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            error_code="RATE_LIMIT_EXCEEDED",
            extra={"retry_after_seconds": retry_after}
        )


# ============= ERROR HANDLERS =============

def create_error_response(
    status_code: int,
    error_code: str,
    detail: str,
    extra: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Crear respuesta de error estandarizada"""
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": detail,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
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
            request_id=request.headers.get("X-Request-ID")
        )
    )


async def http_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handler para excepciones HTTP de Starlette"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            detail=exc.detail,
            request_id=request.headers.get("X-Request-ID")
        )
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handler para errores de validación de Pydantic"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            detail="Request validation failed",
            extra={"errors": errors},
            request_id=request.headers.get("X-Request-ID")
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para excepciones no manejadas (500)"""
    # Log el error completo para debugging
    error_trace = traceback.format_exc()
    print(f"Unhandled exception: {error_trace}")
    
    # En producción, no exponer detalles internos
    from app.core.config import settings
    
    detail = str(exc) if settings.DEBUG else "Internal server error"
    extra = {"trace": error_trace} if settings.DEBUG else None
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            detail=detail,
            extra=extra,
            request_id=request.headers.get("X-Request-ID")
        )
    )


# ============= SETUP EN APP =============

def setup_exception_handlers(app: FastAPI):  
    """Registrar todos los exception handlers en la app"""
    
    # Handlers personalizados
    app.add_exception_handler(APIException, api_exception_handler)
    
    # Handlers de FastAPI/Starlette
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Handler catch-all para errores no manejados
    app.add_exception_handler(Exception, general_exception_handler)


# ============= EJEMPLO DE USO =============

"""
En app/main.py:

from app.api.errors.handlers import setup_exception_handlers

app = FastAPI()
setup_exception_handlers(app)


En tus servicios:

from app.api.errors.http_errors import NotFoundException, ValidationException

class InvoiceService:
    async def get_invoice(self, id: int):
        invoice = await self.repo.get(id)
        
        if not invoice:
            raise NotFoundException("Invoice", id)
        
        return invoice
    
    async def create_invoice(self, data):
        if data.total <= 0:
            raise ValidationException(["Total must be greater than zero"])
        
        # ... lógica


Respuesta de error estandarizada:

{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Invoice with identifier '123' not found",
    "status_code": 404,
    "timestamp": "2026-02-13T10:30:00.000Z",
    "details": {
      "resource": "Invoice",
      "identifier": "123"
    }
  },
  "request_id": "abc-123-def"
}
"""
