import asyncio
import shutil
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.transformer import procesar_archivo_subido
from app.database import get_session
from app.models import Lote
from app.tasks import procesar_archivo_task

# Creamos un "Router" (como una mini-app)
router = APIRouter()

# Asegurar que existe directorio temporal
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

@router.post("/procesar-documento")
async def subir_documento(file: UploadFile = File(...)):
    temp_filename = TEMP_DIR / f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Convertimos a string porque polars/pandas esperan str path usualmente
        resultado = await procesar_archivo_subido(str(temp_filename))

        errores = resultado["errores"]
        validas = resultado["validas"]
        unique_rejected = len({e["id_factura"] for e in errores})

        return {
            "resumen": {
                "total_facturas": len(validas) + unique_rejected,
                "validas": len(validas),
                "rechazadas": unique_rejected
            },
            "errores": errores,
            "procesadas": validas
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if temp_filename.exists():
            os.remove(temp_filename)


@router.post("/emitir-facturas-masivas")
async def emitir_facturas_masivas(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session) # Inyectamos sesión de BD
):
    """
    Pipeline Asíncrono con Celery:
    1. Guardar archivo en disco
    2. Crear registro Lote en BD (PENDIENTE)
    3. Enviar tarea a Celery (procesamiento en background)
    4. Retornar ID de lote y task_id inmediatamente
    """
    # 1. Guardar archivo temporal
    # Usamos resolve() para obtener ruta absoluta y evitar problemas en el worker
    # aunque si comparten FS relativo podria valer, absoluto es mas seguro.
    temp_filename = TEMP_DIR / f"lote_{file.filename}"

    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Registrar Lote (PENDIENTE)
        nuevo_lote = Lote(
            nombre_archivo=file.filename,
            estado="PENDIENTE"
        )
        session.add(nuevo_lote)
        await session.commit()
        await session.refresh(nuevo_lote)

        # 3. Llamar a procesar_archivo_task.delay
        task = procesar_archivo_task.delay(nuevo_lote.id, str(temp_filename.resolve()))

        # 4. Retornar inmediatamente
        return {
            "mensaje": "Procesamiento iniciado",
            "lote_id": nuevo_lote.id,
            "task_id": task.id
        }

    except Exception as e:
        # Si falla antes de encolar, limpiamos
        if temp_filename.exists():
            os.remove(temp_filename)
        return {"error": str(e)}
