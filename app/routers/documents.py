import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.transformer import procesar_archivo_subido, factus_client
import shutil
import os

# Creamos un "Router" (como una mini-app)
router = APIRouter()

@router.post("/procesar-documento")
async def subir_documento(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        resultado_json = await procesar_archivo_subido(temp_filename)
        return {"mensaje": "Procesado con éxito", "total_facturas": len(resultado_json), "datos": resultado_json}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@router.post("/emitir-facturas-masivas")
async def emitir_facturas_masivas(file: UploadFile = File(...)):
    """
    Pipeline Completo:
    1. Upload -> 2. Polars Transform -> 3. Async Parallel Sending -> 4. Report
    """
    temp_filename = f"temp_{file.filename}"
    
    # 1. Guardar archivo
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Transformar con Polars (Super Rápido)
        lote_facturas = await procesar_archivo_subido(temp_filename)
        
        # 3. Enviar a Factus en Paralelo (Concurrency)
        # Creamos una lista de tareas (tasks)
        tareas = []
        for factura in lote_facturas:
            # Programamos el envío, pero no lo ejecutamos todavía
            tarea = factus_client.enviar_factura(factura)
            tareas.append(tarea)
            
        # ¡BOOM! Ejecutamos todas las peticiones al tiempo 🚀
        # asyncio.gather espera a que todas terminen
        resultados = await asyncio.gather(*tareas)
        
        # 4. Compilar reporte
        exitosas = [r for r in resultados if r["status"] in [200, 201]]
        fallidas = [r for r in resultados if r["status"] not in [200, 201]]

        return {
            "resumen": {
                "total_procesadas": len(lote_facturas),
                "enviadas_exito": len(exitosas),
                "fallidas": len(fallidas)
            },
            "detalle_errores": fallidas # Para que sepas qué corregir
        }

    except Exception as e:
        return {"error_critico": str(e)}
        
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)