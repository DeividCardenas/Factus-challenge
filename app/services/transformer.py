import polars as pl
from app.services.api_client import factus_client


# --- LÓGICA DE NEGOCIO (Polars con Archivos Reales) ---
async def procesar_archivo_subido(file_path: str):
    """
    Lee un archivo CSV o Excel desde el disco usando Lazy API de Polars,
    valida la calidad de los datos y lo transforma al formato de Factus.
    Retorna un diccionario con facturas válidas y errores.
    """
    
    # Detectar extensión para saber cómo leerlo
    if file_path.endswith(".csv"):
        # Lazy CSV
        lf = pl.scan_csv(file_path)
    elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
        # INTENTO 1: Usar el motor 'fastexcel' explícito (más rápido en Rust)
        try:
            lf = pl.read_excel(file_path, engine="calamine").lazy()
        except Exception:
            # FALLBACK DE ALTO RENDIMIENTO:
            lf = pl.read_excel(file_path, engine="xlsx2csv").lazy()
    else:
        raise ValueError("Formato no soportado. Usa CSV o Excel.")

    # Agregar índice de fila original para rastreo de errores
    # offset=2 asumiendo cabecera en línea 1, datos empiezan en línea 2 (visual para usuario)
    lf = lf.with_row_index(name="fila_excel", offset=2)

    # Normalizar nombres de columnas a minúsculas
    lf = lf.rename({col: col.lower() for col in lf.collect_schema().names()})

    # Casting inicial necesario para validaciones y procesamiento
    lf = lf.with_columns([
        pl.col("id_factura").cast(pl.String, strict=False),
        pl.col("precio_unitario").cast(pl.Float64, strict=False),
        pl.col("cantidad").cast(pl.Int64, strict=False)
    ])

    # --- VALIDACIÓN DE CALIDAD DE DATOS ---

    # Definir expresiones de validación
    # fill_null(False) asegura que valores nulos cuenten como error
    check_email = pl.col("cliente_email").str.contains("@").fill_null(False)
    check_price = (pl.col("precio_unitario") > 0).fill_null(False)
    check_qty = (pl.col("cantidad") > 0).fill_null(False)

    # Construir columna de motivos de error concatenando strings
    error_expr = pl.when(check_email).then(pl.lit("")).otherwise(pl.lit("Email inválido; ")) + \
                 pl.when(check_price).then(pl.lit("")).otherwise(pl.lit("Precio debe ser > 0; ")) + \
                 pl.when(check_qty).then(pl.lit("")).otherwise(pl.lit("Cantidad debe ser > 0; "))

    # Validar fila individual
    lf_validated = lf.with_columns([
        (check_email & check_price & check_qty).alias("is_valid_row"),
        error_expr.str.strip_chars("; ").alias("motivo_error")
    ])

    # Validar factura completa (Atomicidad): Si una fila falla, toda la factura falla
    lf_atomic = lf_validated.with_columns(
        pl.col("is_valid_row").all().over("id_factura").alias("is_valid_invoice")
    )

    # Separar válidas e inválidas (Lazy)
    valid_lf = lf_atomic.filter(pl.col("is_valid_invoice"))
    error_lf = lf_atomic.filter(~pl.col("is_valid_invoice"))

    # --- PROCESAMIENTO DE ERRORES ---
    # Materializamos solo los errores para iterar y reportar
    error_df = error_lf.collect()

    errores_list = []
    if not error_df.is_empty():
        # En caso de rechazo atómico, algunas filas pueden ser válidas técnicamente,
        # pero se rechazan por pertenecer a una factura inválida.
        error_df = error_df.with_columns(
             pl.when(pl.col("motivo_error") == "")
             .then(pl.lit("Factura rechazada por error en otros ítems"))
             .otherwise(pl.col("motivo_error"))
             .alias("motivo_final")
        )
        
        rows = error_df.iter_rows(named=True)
        for row in rows:
            # Extraemos datos raw excluyendo columnas internas nuestras
            datos_raw = {k: v for k, v in row.items()
                         if k not in ["fila_excel", "is_valid_row", "is_valid_invoice", "motivo_error", "motivo_final"]}

            errores_list.append({
                "fila_index": row["fila_excel"],
                "id_factura": row["id_factura"],
                "motivo": row["motivo_final"],
                "datos_raw": datos_raw
            })

    # --- TRANSFORMACIÓN DE VÁLIDAS (Lógica original) ---
    validas_list = []

    q = (
        valid_lf
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
                pl.lit("0").alias("discount_rate"),

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
            pl.col("total_bruto"),
            pl.col("total_impuestos"),

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
