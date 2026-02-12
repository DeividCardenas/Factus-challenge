import polars as pl
import fastexcel
from app.services.api_client import factus_client


# --- LÓGICA DE NEGOCIO (Polars con Archivos Reales) ---
async def procesar_archivo_subido(file_path: str):
    """
    Lee un archivo CSV o Excel desde el disco usando Lazy API de Polars,
    valida la calidad de los datos con atomicidad estricta y lo transforma.

    Validación Atómica Estricta: Si una fila de una factura falla, TODA la factura se rechaza.
    """
    
    # Detectar extensión para saber cómo leerlo
    if file_path.endswith(".csv"):
        # Lazy CSV
        lf = pl.scan_csv(file_path)
    elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
        try:
            lf = pl.read_excel(file_path, engine="calamine").lazy()
        except Exception:
            lf = pl.read_excel(file_path, engine="xlsx2csv").lazy()
    else:
        raise ValueError("Formato no soportado. Usa CSV o Excel.")

    # Agregar índice de fila original para rastreo de errores
    lf = lf.with_row_index(name="fila_excel", offset=2)

    # Normalizar nombres de columnas a minúsculas
    lf = lf.rename({col: col.lower() for col in lf.collect_schema().names()})

    # Casting inicial necesario para validaciones y procesamiento
    lf = lf.with_columns([
        pl.col("id_factura").cast(pl.String),
        pl.col("precio_unitario").cast(pl.Float64),
        pl.col("cantidad").cast(pl.Int64)
    ])

    # --- VALIDACIÓN DE CALIDAD DE DATOS (REESCRITURA SOLICITADA) ---

    # 1. Crear columna 'es_fila_valida' basada en reglas individuales
    check_email = pl.col("cliente_email").str.contains("@").fill_null(False)
    check_price = (pl.col("precio_unitario") > 0).fill_null(False)
    check_qty = (pl.col("cantidad") > 0).fill_null(False)

    # Construir motivo de error individual
    error_expr = pl.when(check_email).then(pl.lit("")).otherwise(pl.lit("Email inválido; ")) + \
                 pl.when(check_price).then(pl.lit("")).otherwise(pl.lit("Precio debe ser > 0; ")) + \
                 pl.when(check_qty).then(pl.lit("")).otherwise(pl.lit("Cantidad debe ser > 0; "))

    lf_validated_rows = lf.with_columns([
        (check_email & check_price & check_qty).alias("es_fila_valida"),
        error_expr.str.strip_chars("; ").alias("motivo_error")
    ])

    # 2. Paso Clave: Validación Atómica por Factura (Window Function)
    # factura_valida será True SOLO si todas las filas del mismo id_factura son válidas
    lf_atomic = lf_validated_rows.with_columns(
        pl.col("es_fila_valida").all().over("id_factura").alias("factura_valida")
    )

    # Materializar dataframes para separar flujos
    df = lf_atomic.collect()

    # 3. Filtrado Final
    # df_validos: Solo facturas completamente válidas
    valid_df = df.filter(pl.col("factura_valida"))

    # df_errores: Facturas con al menos un error (incluye filas "buenas" de facturas malas)
    error_df = df.filter(~pl.col("factura_valida"))

    # --- PROCESAMIENTO DE ERRORES ---
    errores_list = []
    if not error_df.is_empty():
        # En caso de rechazo atómico, marcamos las filas "válidas" como rechazadas por asociación
        error_df = error_df.with_columns(
             pl.when(pl.col("motivo_error") == "")
             .then(pl.lit("Factura rechazada por error en otros ítems"))
             .otherwise(pl.col("motivo_error"))
             .alias("motivo_final")
        )
        
        rows = error_df.iter_rows(named=True)
        for row in rows:
            # Extraemos datos raw excluyendo columnas internas
            datos_raw = {k: v for k, v in row.items()
                         if k not in ["fila_excel", "es_fila_valida", "factura_valida", "motivo_error", "motivo_final"]}

            errores_list.append({
                "fila_index": row["fila_excel"],
                "id_factura": row["id_factura"],
                "motivo": row["motivo_final"],
                "datos_raw": datos_raw
            })

    # --- TRANSFORMACIÓN DE VÁLIDAS ---
    validas_list = []
    if not valid_df.is_empty():
        q = (
            valid_df.lazy()
            # 2. CÁLCULOS
            .with_columns([
                (pl.col("precio_unitario") * pl.col("cantidad")).alias("total_linea"),
                (pl.col("precio_unitario") * pl.col("cantidad") * (pl.col("iva_porcentaje") / 100)).alias("valor_impuesto")
            ])

            # 3. ESTRUCTURA ITEM
            .with_columns(
                pl.struct([
                    pl.col("producto").alias("code_reference"),
                    pl.col("producto").alias("name"),
                    pl.col("cantidad").alias("quantity"),
                    pl.col("precio_unitario").alias("price"),
                    pl.col("iva_porcentaje").alias("tax_rate"),
                    pl.lit("1").alias("discount_rate"),

                    pl.struct([
                        pl.lit("1").alias("code"),
                        pl.lit("IVA").alias("name"),
                        pl.col("iva_porcentaje").alias("rate"),
                        pl.col("valor_impuesto").alias("amount")
                    ]).alias("taxes")

                ]).alias("item_struct")
            )

            .group_by(["id_factura", "cliente_nombre", "cliente_email"])
            .agg([
                pl.col("item_struct").alias("items"),
                pl.col("total_linea").sum().alias("total_bruto"),
                pl.col("valor_impuesto").sum().alias("total_impuestos")
            ])

            # 4. ESTRUCTURA FINAL
            .select([
                pl.col("id_factura").alias("numbering_range_id"),
                pl.col("id_factura").alias("reference_code"),
                pl.lit("1").alias("payment_form"),
                pl.lit("10").alias("payment_method_code"),

                pl.struct([
                    pl.col("cliente_nombre").alias("names"),
                    pl.col("cliente_email").alias("email"),
                    pl.lit("1").alias("identification"),
                    pl.lit("13").alias("identification_document_id"),
                    pl.lit("2").alias("legal_organization_id")
                ]).alias("customer"),

                pl.col("items")
            ])
        )
        validas_list = q.collect().to_dicts()

    return {
        "validas": validas_list,
        "errores": errores_list
    }
