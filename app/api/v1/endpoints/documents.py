import asyncio
import shutil
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.transformer import procesar_archivo_subido
from app.core.database import get_session
from app.models import Lote, Factura, User
from app.core.deps import get_current_user
from app.models import Lote
from app.services.tasks import procesar_archivo_task
from app.repositories.factura_repository import FacturaRepository
from app.repositories import LoteRepository
from app.schemas import ProcessResult, BatchUploadResponse
from app.api.errors.http_errors import ValidationException

# Creamos un "Router" (como una mini-app)
router = APIRouter()

# Asegurar que existe directorio temporal
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


@router.post("/procesar-documento", status_code=status.HTTP_200_OK)
async def subir_documento(file: UploadFile = File(...)):
    """
    Procesar documento de prueba (sin requerir autenticación).
    Retorna errores y facturas válidas.
    """
    # Validar tipo de archivo
    allowed_extensions = {".csv", ".xlsx", ".xls"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise ValidationException([
            f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
        ])

    temp_filename = TEMP_DIR / f"temp_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convertimos a string porque polars/pandas esperan str path
        resultado = await procesar_archivo_subido(str(temp_filename))

        errores = resultado["errores"]
        validas = resultado["validas"]
        unique_rejected = len({e["id_factura"] for e in errores})

        return {
            "resumen": {
                "total_facturas": len(validas) + unique_rejected,
                "validas": len(validas),
                "rechazadas": unique_rejected,
            },
            "errores": errores,
            "procesadas": validas,
        }
    except Exception as e:
        raise ValidationException([str(e)])
    finally:
        if temp_filename.exists():
            os.remove(temp_filename)


@router.post("/emitir-facturas-masivas", response_model=BatchUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def emitir_facturas_masivas(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Pipeline Asíncrono con Celery:
    1. Guardar archivo en disco
    2. Crear registro Lote en BD
    3. Enviar tarea a Celery (procesamiento en background)
    4. Retornar ID de lote y task_id inmediatamente
    
    Con mejoras:
    - Repository pattern
    - Validación mejorada
    - Excepciones personalizadas
    """
    # Validar tipo de archivo
    allowed_extensions = {".csv", ".xlsx", ".xls"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise ValidationException([
            f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
        ])

    # 1. Guardar archivo temporal
    temp_filename = TEMP_DIR / f"lote_{file.filename}"

    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Registrar Lote usando repository
        lote_repo = LoteRepository(session)
        nuevo_lote = Lote(
            nombre_archivo=file.filename,
            estado="PENDIENTE"
        )
        lote_guardado = await lote_repo.create(nuevo_lote)

        # 3. Llamar a procesar_archivo_task.delay
        task = procesar_archivo_task.delay(
            lote_guardado.id, 
            str(temp_filename.resolve())
        )

        # 4. Retornar inmediatamente
        return BatchUploadResponse(
            mensaje="Procesamiento iniciado",
            lote_id=lote_guardado.id,
            task_id=task.id,
            estimated_time=300  # 5 minutos estimados
        )

    except Exception as e:
        # Si falla antes de encolar, limpiamos
        if temp_filename.exists():
            os.remove(temp_filename)
        raise ValidationException([str(e)])
