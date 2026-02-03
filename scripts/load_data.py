#!/usr/bin/env python3
"""
TORRE CONTROL - Pipeline de Ingesta de Datos (Fase 2.1)
===========================================================

Propósito: Cargar DataCoSupplyChainDataset.csv → PostgreSQL stg_raw_orders

Características Senior:
- Manejo de encoding ISO-8859-1 (caracteres latinos en el dataset de DataCo)
- Sanitización automática de nombres de columnas (snake_case)
- Chunking por lotes para eficiencia en datasets grandes
- Logging detallado de cada etapa del pipeline
- Control de errores robusto

Uso:
    python scripts/load_data.py
"""

# Configurar encoding de salida para Windows
import io
import os
import sys
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- CONFIGURACIÓN ---
# Ajusta el puerto 5433 según tu configuración exitosa de Docker
DB_USER = "admin"
DB_PASSWORD = "adminpassword"
DB_HOST = "localhost"
DB_PORT = "5433"  # Puerto Docker actualizado
DB_NAME = "supply_chain_dw"
DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

CSV_PATH = os.path.join("data", "raw", "DataCoSupplyChainDataset.csv")
STAGING_TABLE = "stg_raw_orders"
SCHEMA = "dw"

# --- LOGGING UTILITIES ---


def log(message: str, level: str = "INFO"):
    """Logging con timestamps e ícono según nivel"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icons = {
        "INFO": "[INFO]",
        "SUCCESS": "[OK]",
        "ERROR": "[ERROR]",
        "WARNING": "[WARN]",
        "PROGRESS": "[LOAD]",
        "DATA": "[DATA]",
        "FILE": "[FILE]",
        "ROCKET": "[START]"
    }
    icon = icons.get(level, "[*]")
    print(f"{icon} [{timestamp}] {level:8s} | {message}")

# --- MAIN PIPELINE ---


def run_pipeline():
    """Pipeline completo: Extract → Transform → Load"""

    log("Iniciando Pipeline de Ingesta (Fase 2.1)...", "ROCKET")
    print()

    # ============================================================
    # ETAPA 1: CONEXIÓN A BASE DE DATOS
    # ============================================================
    try:
        log(f"Conectando a PostgreSQL ({DB_HOST}:{DB_PORT})...", "PROGRESS")
        engine = create_engine(DB_URI, echo=False)

        # Test de conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        log(
            f"Conexión a PostgreSQL exitosa. Schema: {SCHEMA}, Tabla: {STAGING_TABLE}", "SUCCESS")
        print()
    except (OperationalError, SQLAlchemyError) as e:
        log(f"Error conectando a BD: {e}", "ERROR")
        sys.exit(1)

    # ============================================================
    # ETAPA 2: LECTURA DEL CSV (EXTRACT)
    # ============================================================
    try:
        log(f"Leyendo archivo: {CSV_PATH}", "FILE")

        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(
                f"No se encuentra el archivo en {CSV_PATH}")

        # Obtener tamaño del archivo
        file_size_mb = os.path.getsize(CSV_PATH) / (1024 * 1024)
        log(f"Tamaño del archivo: {file_size_mb:.2f} MB", "DATA")

        # El dataset DataCo tiene encoding latin-1
        df = pd.read_csv(CSV_PATH, encoding='ISO-8859-1')

        log("Archivo leído exitosamente.", "SUCCESS")
        log(f"Dimensiones: {len(df):,} filas × {len(df.columns)} columnas", "DATA")
        print()
    except FileNotFoundError as e:
        log(f"Error: {e}", "ERROR")
        sys.exit(1)
    except (pd.errors.ParserError, OSError, UnicodeDecodeError) as e:
        log(f"Error leyendo CSV: {e}", "ERROR")
        sys.exit(1)

    # ============================================================
    # ETAPA 3: LIMPIEZA DE NOMBRES (TRANSFORM - LIGHT)
    # ============================================================
    try:
        log("Normalizando nombres de columnas (snake_case)...", "PROGRESS")

        original_columns = list(df.columns)
        df.columns = [
            c.lower()           # Minúsculas
             .strip()           # Quitar espacios
             .replace(' ', '_')  # Espacios → underscores
             .replace('-', '_')  # Guiones → underscores
            for c in df.columns
        ]

        new_columns = list(df.columns)

        # Mostrar mapeo de columnas
        log("Columnas originales → normalizadas:", "INFO")
        for orig, new in zip(original_columns[:5], new_columns[:5]):
            print(f"   • '{orig}' → '{new}'")
        if len(original_columns) > 5:
            print(f"   • ... ({len(original_columns) - 5} más)")

        log(f"Total de columnas normalizadas: {len(df.columns)}", "SUCCESS")
        print()
    except (AttributeError, ValueError) as e:
        log(f"Error normalizando columnas: {e}", "ERROR")
        sys.exit(1)

    # ============================================================
    # ETAPA 4: CARGA A STAGING (LOAD)
    # ============================================================
    try:
        log(f"Cargando {len(df):,} filas a tabla '{SCHEMA}.{STAGING_TABLE}'...", "PROGRESS")

        # Usar 'replace' para recrear la tabla cada vez (útil para full loads)
        df.to_sql(
            STAGING_TABLE,
            engine,
            schema=SCHEMA,
            if_exists='replace',  # Recrea la tabla (DELETE + CREATE)
            index=False,
            method='multi',        # Inserción multi-row para velocidad
            chunksize=10000        # Procesar en lotes de 10K filas
        )

        log("Carga completada exitosamente.", "SUCCESS")
        print()
    except (SQLAlchemyError, ValueError) as e:
        log(f"Error en la carga SQL: {e}", "ERROR")
        sys.exit(1)

    # ============================================================
    # ETAPA 5: VALIDACIÓN POST-CARGA (QA)
    # ============================================================
    try:
        log("Ejecutando validaciones post-carga...", "PROGRESS")

        with engine.connect() as conn:
            # Contar filas en tabla
            count_result = conn.execute(
                text(f"SELECT COUNT(*) as total FROM {SCHEMA}.{STAGING_TABLE}")
            )
            total_rows = count_result.fetchone()[0]

            log(f"Total de filas en BD: {total_rows:,}", "DATA")

            # Verificar si coincide
            if total_rows == len(df):
                log(
                    f"[OK] Conteo de filas coincide con CSV ({total_rows:,} filas)", "SUCCESS")
            else:
                log(
                    f"[WARN] Discrepancia: CSV={len(df):,}, BD={total_rows:,}", "WARNING")

            # Obtener columnas en BD
            inspector = inspect(engine)
            columns = inspector.get_columns(STAGING_TABLE, schema=SCHEMA)
            log(f"Columnas creadas en BD: {len(columns)}", "DATA")

            print()
    except (SQLAlchemyError, KeyError, IndexError) as e:
        log(f"Error en validación: {e}", "ERROR")
        sys.exit(1)

    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    print("=" * 70)
    log("PIPELINE COMPLETADO EXITOSAMENTE", "SUCCESS")
    print("=" * 70)
    print(f"""
RESUMEN DE EJECUCION:
============================================================================
  CSV Fuente:        {CSV_PATH}
  Tamaño:            {file_size_mb:.2f} MB
  Filas Leidas:      {len(df):,}
  Columnas:          {len(df.columns)}
  
  Destino BD:        PostgreSQL ({DB_HOST}:{DB_PORT})
  Base de Datos:     {DB_NAME}
  Schema:            {SCHEMA}
  Tabla:             {STAGING_TABLE}
  Filas Cargadas:    {total_rows:,}
  Encoding:          ISO-8859-1
  Metodo:            Multi-row insert con chunking (10K por lote)
============================================================================

Proximos Pasos (Fase 2.2):
   1. Ejecutar queries de verificacion en SQLTools
   2. Verificar duplicados en order_item_id
   3. Proceder con transformacion a dimensiones (dim_customer, dim_geography, etc.)

Queries Recomendados:
   SELECT COUNT(*) FROM dw.stg_raw_orders;
   SELECT * FROM dw.stg_raw_orders LIMIT 5;
   SELECT order_item_id, COUNT(*) FROM dw.stg_raw_orders GROUP BY order_item_id HAVING COUNT(*) > 1;
""")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
