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
        resultado = await procesar_archivo_subido(temp_filename)

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
        # resultado ahora es {"validas": [...], "errores": [...]}
        resultado_proceso = await procesar_archivo_subido(temp_filename)

        lote_facturas = resultado_proceso["validas"]
        errores_validacion = resultado_proceso["errores"]
        
        # 3. Enviar a Factus en Paralelo (Concurrency)
        # Solo enviamos las válidas
        tareas = []
        for factura in lote_facturas:
            # Programamos el envío, pero no lo ejecutamos todavía
            tarea = factus_client.enviar_factura(factura)
            tareas.append(tarea)
            
        # ¡BOOM! Ejecutamos todas las peticiones al tiempo 🚀
        resultados_envio = []
        if tareas:
            resultados_envio = await asyncio.gather(*tareas)
        
        # 4. Compilar reporte
        exitosas = [r for r in resultados_envio if r["status"] in [200, 201]]
        fallidas_envio = [r for r in resultados_envio if r["status"] not in [200, 201]]

        # Métricas
        unique_rejected_validation = len({e["id_factura"] for e in errores_validacion})
        total_validas_transform = len(lote_facturas)
        total_enviadas_exito = len(exitosas)
        total_fallidas_envio = len(fallidas_envio)

        total_facturas = total_validas_transform + unique_rejected_validation

        # Unificar lista de errores
        # Agregamos una marca de origen al error si es de envío
        errores_envio_formateados = []
        for f in fallidas_envio:
            errores_envio_formateados.append({
                "origen": "API Factus",
                "detalle": f
            })

        lista_errores_completa = errores_validacion + errores_envio_formateados

        return {
            "resumen": {
                "total_facturas": total_facturas,
                "validas": total_enviadas_exito,
                "rechazadas": unique_rejected_validation + total_fallidas_envio
            },
            "errores": lista_errores_completa,
            "procesadas": exitosas
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error_critico": str(e)}
        
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
