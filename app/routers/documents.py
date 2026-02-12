import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.transformer import procesar_archivo_subido, factus_client
from app.database import get_session
from app.models import Lote, Factura
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
async def emitir_facturas_masivas(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session) # Inyectamos sesión de BD
):
    """
    Pipeline Completo CON PERSISTENCIA:
    1. Registrar Lote (PROCESANDO)
    2. Polars Transform
    3. Guardar Rechazados
    4. Async Parallel Sending
    5. Guardar Resultados API
    6. Cerrar Lote (COMPLETADO)
    """
    temp_filename = f"temp_{file.filename}"
    
    # 1. Guardar archivo temporal
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    nuevo_lote = None
    try:
        # --- PASO 1: REGISTRAR LOTE ---
        nuevo_lote = Lote(
            nombre_archivo=file.filename,
            estado="PROCESANDO"
        )
        session.add(nuevo_lote)
        await session.commit()
        await session.refresh(nuevo_lote)

        # --- PASO 2: TRANSFORMAR (Polars) ---
        resultado_proceso = await procesar_archivo_subido(temp_filename)
        lote_facturas = resultado_proceso["validas"]
        errores_validacion = resultado_proceso["errores"]

        # Actualizar total registros
        unique_rejected_ids = {e["id_factura"] for e in errores_validacion}
        total_docs = len(lote_facturas) + len(unique_rejected_ids)
        nuevo_lote.total_registros = total_docs
        session.add(nuevo_lote)

        # --- PASO 3: GUARDAR RECHAZADOS (Bulk Insert) ---
        facturas_rechazadas_db = []
        rechazados_map = {}
        for err in errores_validacion:
            fid = err["id_factura"]
            if fid not in rechazados_map:
                rechazados_map[fid] = err

        for fid, err_data in rechazados_map.items():
            raw = err_data.get("datos_raw", {})
            # Extraer total si posible
            total_calc = 0.0
            try:
                p = float(raw.get("precio_unitario", 0))
                q = float(raw.get("cantidad", 0))
                total_calc = p * q
            except:
                pass

            email = raw.get("cliente_email", "desconocido@error.com")

            facturas_rechazadas_db.append(Factura(
                lote_id=nuevo_lote.id,
                reference_code=fid,
                cliente_email=email,
                total=total_calc,
                estado="RECHAZADA",
                motivo_rechazo=err_data["motivo"],
                api_response=None
            ))

        if facturas_rechazadas_db:
            session.add_all(facturas_rechazadas_db)
            await session.commit() # Guardamos rechazados

        # --- PASO 4: ENVIAR A API (Async) ---
        tareas = []
        for factura in lote_facturas:
            tarea = factus_client.enviar_factura(factura)
            tareas.append(tarea)
            
        resultados_envio = []
        if tareas:
            resultados_envio = await asyncio.gather(*tareas)
        
        # --- PASO 5: GUARDAR RESULTADOS API ---
        facturas_procesadas_db = []

        # zip para correlacionar solicitud con respuesta
        for factura_data, resp in zip(lote_facturas, resultados_envio):
            es_exito = resp["status"] in [200, 201]
            estado_final = "ENVIADA" if es_exito else "ERROR_API"

            ref = str(factura_data.get("numbering_range_id"))
            # Extraer email y total del dict transformado (ver transformer.py)
            # transformer.py devuelve customer -> email, y total_bruto
            cust = factura_data.get("customer", {})
            email = cust.get("email", "")
            total = factura_data.get("total_bruto", 0.0)

            motivo = None
            if not es_exito:
                motivo = f"API Error: {resp.get('status')}"

            facturas_procesadas_db.append(Factura(
                lote_id=nuevo_lote.id,
                reference_code=ref,
                cliente_email=email,
                total=total,
                estado=estado_final,
                motivo_rechazo=motivo,
                api_response=resp # JSONB
            ))

        if facturas_procesadas_db:
            session.add_all(facturas_procesadas_db)

        # --- PASO 6: CERRAR LOTE ---
        nuevo_lote.estado = "COMPLETADO"
        session.add(nuevo_lote)

        await session.commit()

        # Retorno simple como pide el requerimiento
        return {"lote_id": nuevo_lote.id, "mensaje": "Procesamiento finalizado"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Si falla algo crítico, marcamos lote como ERROR
        if nuevo_lote:
            try:
                nuevo_lote.estado = "ERROR"
                session.add(nuevo_lote)
                await session.commit()
            except:
                pass
        return {"error_critico": str(e)}
        
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
