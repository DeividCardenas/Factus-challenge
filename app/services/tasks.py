import asyncio
import os
import traceback
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.celery_app import celery_app
from app.core.database import DATABASE_URL
from app.models import Lote, Factura
from app.services.transformer import procesar_archivo_subido
from app.services.api_client import factus_client

@celery_app.task(name="procesar_archivo_task")
def procesar_archivo_task(lote_id: int, file_path: str):
    """
    Tarea Celery que envuelve la lógica asíncrona usando asyncio.run()
    """
    try:
        asyncio.run(_procesar_archivo_async(lote_id, file_path))
    except Exception as e:
        print(f"Error fatal en tarea Celery: {e}")
        traceback.print_exc()

async def _procesar_archivo_async(lote_id: int, file_path: str):
    # Creamos un motor específico para esta tarea para evitar conflictos de Event Loop
    # con el motor global si se usara asyncio.run() repetidamente.
    local_engine = create_async_engine(DATABASE_URL, echo=False)

    async_session = sessionmaker(
        local_engine, class_=AsyncSession, expire_on_commit=False
    )

    lote = None
    try:
        async with async_session() as session:
            # 1. Obtener el lote y actualizar estado a PROCESANDO
            lote = await session.get(Lote, lote_id)
            if not lote:
                print(f"Lote {lote_id} no encontrado.")
                return

            lote.estado = "PROCESANDO"
            session.add(lote)
            await session.commit()
            await session.refresh(lote)

            try:
                # 2. Transformar (Polars)
                # Nota: procesar_archivo_subido es async
                resultado_proceso = await procesar_archivo_subido(file_path)
                lote_facturas = resultado_proceso["validas"]
                errores_validacion = resultado_proceso["errores"]

                # Actualizar total registros
                unique_rejected_ids = {e["id_factura"] for e in errores_validacion}
                total_docs = len(lote_facturas) + len(unique_rejected_ids)
                lote.total_registros = total_docs
                session.add(lote)

                # 3. Guardar Rechazados (Bulk Insert)
                facturas_rechazadas_db = []
                rechazados_map = {}
                for err in errores_validacion:
                    fid = err["id_factura"]
                    if fid not in rechazados_map:
                        rechazados_map[fid] = err

                for fid, err_data in rechazados_map.items():
                    raw = err_data.get("datos_raw", {})
                    total_calc = 0.0
                    try:
                        p = float(raw.get("precio_unitario", 0))
                        q = float(raw.get("cantidad", 0))
                        total_calc = p * q
                    except:
                        pass

                    email = raw.get("cliente_email", "desconocido@error.com")

                    facturas_rechazadas_db.append(Factura(
                        lote_id=lote.id,
                        reference_code=fid,
                        cliente_email=email,
                        total=total_calc,
                        estado="RECHAZADA",
                        motivo_rechazo=err_data["motivo"],
                        api_response=None
                    ))

                if facturas_rechazadas_db:
                    session.add_all(facturas_rechazadas_db)
                    await session.commit()

                # 4. Enviar a API (Async)
                tareas_envio = []
                for factura in lote_facturas:
                    tarea = factus_client.enviar_factura(factura)
                    tareas_envio.append(tarea)

                resultados_envio = []
                if tareas_envio:
                    resultados_envio = await asyncio.gather(*tareas_envio)

                # 5. Guardar Resultados API
                facturas_procesadas_db = []
                # zip para correlacionar solicitud con respuesta
                for factura_data, resp in zip(lote_facturas, resultados_envio):
                    es_exito = resp["status"] in [200, 201]
                    estado_final = "ENVIADA" if es_exito else "ERROR_API"

                    ref = str(factura_data.get("numbering_range_id"))
                    cust = factura_data.get("customer", {})
                    email = cust.get("email", "")
                    total = factura_data.get("total_bruto", 0.0)

                    motivo = None
                    if not es_exito:
                        motivo = f"API Error: {resp.get('status')}"

                    facturas_procesadas_db.append(Factura(
                        lote_id=lote.id,
                        reference_code=ref,
                        cliente_email=email,
                        total=total,
                        estado=estado_final,
                        motivo_rechazo=motivo,
                        api_response=resp
                    ))

                if facturas_procesadas_db:
                    session.add_all(facturas_procesadas_db)

                # 6. Cerrar Lote
                lote.estado = "COMPLETADO"
                session.add(lote)
                await session.commit()

            except Exception as e:
                import traceback
                traceback.print_exc()
                # Si lote fue obtenido, actualizamos estado
                if lote:
                    lote.estado = "ERROR"
                    session.add(lote)
                    try:
                        await session.commit()
                    except:
                        pass
    except Exception as outer_e:
        print(f"Error en _procesar_archivo_async (outer): {outer_e}")
        # Aquí lote podría ser None o no, pero si estamos fuera del async with, la sesión está cerrada.
        # No podemos usar 'session' aquí.
        # El manejo de error dentro del async with cubre la lógica de negocio.
        pass

    finally:
        # Cerrar el motor local
        await local_engine.dispose()

        # Limpieza archivo temporal
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"No se pudo eliminar el archivo temporal {file_path}: {e}")
