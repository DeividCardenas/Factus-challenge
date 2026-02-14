"""
Excepciones personalizadas para la API.
Proporcionan mejor contexto y manejo de errores centralizado.
"""

from typing import Any, Dict, List, Optional
from fastapi import status


class APIException(Exception):
    """Excepción base para todas las excepciones de la API"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        extra: Optional[Dict[str, Any]] = None,
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
            extra={"resource": resource, "identifier": str(identifier)},
        )


class ValidationException(APIException):
    """Error de validación de negocio (422)"""

    def __init__(self, errors: List[str]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation failed",
            error_code="VALIDATION_ERROR",
            extra={"errors": errors},
        )
        self.errors = errors


class UnauthorizedException(APIException):
    """No autenticado (401)"""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(APIException):
    """Sin permisos (403)"""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
        )


class ConflictException(APIException):
    """Conflicto de recursos (409)"""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
        )


class ExternalServiceException(APIException):
    """Error en servicio externo (502)"""

    def __init__(self, service: str, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External service '{service}' failed: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            extra={"service": service, "message": message},
        )


class RateLimitException(APIException):
    """Límite de tasa excedido (429)"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            error_code="RATE_LIMIT_EXCEEDED",
            extra={"retry_after_seconds": retry_after},
        )
