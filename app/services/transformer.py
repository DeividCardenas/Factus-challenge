import polars as pl
import fastexcel
from app.services.api_client import factus_client


# --- LÓGICA DE NEGOCIO (Polars con Archivos Reales) ---
async def procesar_archivo_subido(file_path: str):
    """
    Lee un archivo CSV o Excel desde el disco usando Lazy API de Polars
    y lo transforma al formato de Factus.
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
            # Si fastexcel falla por versión, usamos 'calamine' (el motor Rust nativo)
            # Esto suele ser igual de rápido.
            lf = pl.read_excel(file_path, engine="xlsx2csv").lazy()
    else:
        raise ValueError("Formato no soportado. Usa CSV o Excel.")

    # --- AQUI EMPIEZA LA MAGIA DE POLARS (Igual que antes) ---
    q = (
        lf
        .rename({col: col.lower() for col in lf.collect_schema().names()})
        
        # 1. CASTING IMPORTANTE: Factus pide strings en códigos
        .with_columns([
            pl.col("id_factura").cast(pl.String),
            pl.col("precio_unitario").cast(pl.Float64),
            pl.col("cantidad").cast(pl.Int64)
        ])

        # 2. CÁLCULOS (Igual que antes)
        .with_columns([
            (pl.col("precio_unitario") * pl.col("cantidad")).alias("total_linea"),
            (pl.col("precio_unitario") * pl.col("cantidad") * (pl.col("iva_porcentaje") / 100)).alias("valor_impuesto")
        ])

        # 3. ESTRUCTURA ITEM CON CÓDIGOS DIAN (Aquí está la mejora)
        .with_columns(
            pl.struct([
                pl.col("producto").alias("code_reference"), # Usamos el nombre como referencia
                pl.col("producto").alias("name"),
                pl.col("cantidad").alias("quantity"),
                pl.col("precio_unitario").alias("price"),
                pl.col("iva_porcentaje").alias("tax_rate"),
                pl.lit("1").alias("discount_rate"), # Descuento 0 por defecto
                
                # Anidamos el impuesto como pide Factus a veces (Taxes)
                pl.struct([
                    pl.lit("1").alias("code"), # 01 es IVA
                    pl.lit("IVA").alias("name"),
                    pl.col("iva_porcentaje").alias("rate"),
                    pl.col("valor_impuesto").alias("amount")
                ]).alias("taxes") 
                
            ]).alias("item_struct")
        )

        .group_by(["id_factura", "cliente_nombre", "cliente_email"])
        .agg([
            pl.col("item_struct").alias("items"),
            pl.col("total_linea").sum().alias("total_bruto"), # Esto suele ser legal_monetary_totals
            pl.col("valor_impuesto").sum().alias("total_impuestos")
        ])

        # 4. ESTRUCTURA FINAL CON DATOS DE CABECERA OBLIGATORIOS
        .select([
            pl.col("id_factura").alias("numbering_range_id"), # Ojo: Aquí iría el ID del rango que te den
            pl.col("id_factura").alias("reference_code"),
            pl.lit("1").alias("payment_form"), # 1 = Contado
            pl.lit("10").alias("payment_method_code"), # 10 = Efectivo
            
            # Cliente
            pl.struct([
                pl.col("cliente_nombre").alias("names"),
                pl.col("cliente_email").alias("email"),
                pl.lit("1").alias("identification"), # Dummy si no viene en CSV
                pl.lit("13").alias("identification_document_id"), # 13 = Cédula
                pl.lit("2").alias("legal_organization_id") # 2 = Persona Natural
            ]).alias("customer"),

            pl.col("items")
        ])
    )

    return q.collect().to_dicts()