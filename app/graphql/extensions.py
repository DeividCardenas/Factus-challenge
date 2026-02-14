"""GraphQL Extensions - Custom error handling and context enrichment"""

from typing import Any, Dict, Optional
from strawberry.extensions import SchemaExtension
from strawberry.types import ExecutionContext
import logging

from app.api.errors.http_errors import (
    NotFoundException,
    ValidationException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ExternalServiceException,
)

logger = logging.getLogger(__name__)


class CustomErrorHandling(SchemaExtension):
    """
    Custom schema extension que intercepta excepciones durante la ejecución de GraphQL
    y las mapea a errores estandarizados formato GraphQL.
    
    Propósito:
    - Prevenir N+1: Captura errores de relaciones
    - Mapear excepciones custom a ExecutionError
    - Normalizar respuesta de errores
    - Preservar información de debugging
    
    Problemas Resueltos:
    1. Sin extension: Custom exceptions → 500 Internal Server Error
    2. Con extension: Custom exceptions → Proper GraphQL error format con tipo y mensaje
    """

    async def request_started(self, context: ExecutionContext) -> None:
        """Hook ejecutado al inicio de la request GraphQL"""
        # Aquí puedes enrichar el contexto con datos adicionales si necesario
        # Ej: timing, request ID, etc
        pass

    async def request_finished(self, context: ExecutionContext) -> None:
        """Hook ejecutado al finalizar la request GraphQL"""
        # Aquí puedes hacer logging o limpieza si necesario
        pass

    async def has_errors(self, context: ExecutionContext, errors: list) -> None:
        """
        Hook ejecutado cuando hay errores en la ejecución.
        Este es el lugar perfecto para interceptar y mapear excepciones.
        """
        if not errors:
            return

        # Mapear y transformar errores
        for error in errors:
            self._transform_error(error, context)

    @staticmethod
    def _transform_error(error: Any, context: ExecutionContext) -> None:
        """
        Transforma excepciones originales en errores GraphQL estandarizados.
        
        Mapeo de excepciones:
        - NotFoundException → 404 Not Found
        - ValidationException → 422 Unprocessable Entity
        - UnauthorizedException → 401 Unauthorized
        - ForbiddenException → 403 Forbidden
        - ConflictException → 409 Conflict
        - ExternalServiceException → 502 Bad Gateway
        """
        original_error = error.original_error if hasattr(error, 'original_error') else None
        
        if not original_error:
            # Si no hay error original, mantener el error como está
            return

        # Transmutar excepciones custom a extensiones GraphQL
        error_extensions = _map_exception_to_extensions(original_error)
        
        if error_extensions:
            # Enriquecer el error con extensiones
            if not hasattr(error, 'extensions') or error.extensions is None:
                error.extensions = {}
            
            error.extensions.update(error_extensions)
            
            # Actualizar mensaje si es necesario
            error.message = str(original_error)
            
            logger.debug(
                f"Error mapeado: {type(original_error).__name__} → "
                f"{error_extensions.get('code')}"
            )


def _map_exception_to_extensions(exception: Exception) -> Optional[Dict[str, Any]]:
    """
    Mapea excepciones custom a extensiones GraphQL estandarizadas.
    
    Retorna dict con:
    - code: Código de error (para cliente)
    - category: Categoría (validation, auth, database, etc)
    - statusCode: HTTP status equivalente
    - timestamp: Cuando ocurrió el error
    """
    from datetime import datetime
    
    timestamp = datetime.utcnow().isoformat()
    
    # Mapeo de excepciones
    exception_mappings = {
        NotFoundException: {
            "code": "ENTITY_NOT_FOUND",
            "category": "not_found",
            "statusCode": 404,
        },
        ValidationException: {
            "code": "VALIDATION_ERROR",
            "category": "validation",
            "statusCode": 422,
        },
        UnauthorizedException: {
            "code": "AUTHENTICATION_ERROR",
            "category": "auth",
            "statusCode": 401,
        },
        ForbiddenException: {
            "code": "PERMISSION_ERROR",
            "category": "auth",
            "statusCode": 403,
        },
        ConflictException: {
            "code": "DUPLICATE_ERROR",
            "category": "conflict",
            "statusCode": 409,
        },
        ExternalServiceException: {
            "code": "EXTERNAL_SERVICE_ERROR",
            "category": "external",
            "statusCode": 502,
        },
    }
    
    # Buscar mapeo para la excepción
    for exception_class, mapping in exception_mappings.items():
        if isinstance(exception, exception_class):
            return {
                **mapping,
                "timestamp": timestamp,
                "message": str(exception),
            }
    
    # Si no hay mapeo, retornar None (error genérico)
    return None


class PerformanceMonitoring(SchemaExtension):
    """
    Extension que monitorea el performance de queries GraphQL.
    Útil para detectar N+1 problems y queries lentas.
    """

    async def request_started(self, context: ExecutionContext) -> None:
        """Iniciamos timing cuando comienza la request"""
        import time
        context.request_started_at = time.time()

    async def request_finished(self, context: ExecutionContext) -> None:
        """Calculamos tiempo total al finalizar"""
        import time
        if hasattr(context, 'request_started_at'):
            elapsed_ms = (time.time() - context.request_started_at) * 1000
            
            # Log si es query lenta (> 500ms)
            if elapsed_ms > 500:
                logger.warning(
                    f"Slow GraphQL query detected: {elapsed_ms:.2f}ms\n"
                    f"Query: {context.query}"
                )
