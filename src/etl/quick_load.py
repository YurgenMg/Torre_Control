#!/usr/bin/env python3
"""
Carga simple y directa del CSV a PostgreSQL
Sin emojis, sin stdout buffering issues
"""

import sys

import pandas as pd
from sqlalchemy import create_engine

# Config
DB_URI = "postgresql://admin:adminpassword@localhost:5433/supply_chain_dw"
CSV_PATH = "data/raw/DataCoSupplyChainDataset.csv"
CHUNK_SIZE = 50000

try:
    # Conexión
    print("[*] Conectando a PostgreSQL...")
    engine = create_engine(DB_URI)
    print("[OK] Conectado")

    # Leer CSV
    print(f"[*] Leyendo {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, encoding='ISO-8859-1')
    print(f"[OK] Leidas {len(df):,} filas, {len(df.columns)} columnas")

    # Normalizar columnas
    print("[*] Normalizando nombres de columnas...")
    df.columns = [c.lower().strip().replace(' ', '_').replace(
        '-', '_').replace('(', '').replace(')', '') for c in df.columns]
    print(f"[OK] {len(df.columns)} columnas normalizadas")

    # Cargar a BD
    print("[*] Cargando a dw.stg_raw_orders...")
    df.to_sql('stg_raw_orders', engine, schema='dw',
              if_exists='replace', index=False, chunksize=CHUNK_SIZE)
    print("[OK] Cargado exitosamente")

    # Verificar
    print("[*] Verificando...")
    with engine.connect() as conn:
        result = conn.execute("SELECT COUNT(*) FROM dw.stg_raw_orders")
        count = result.fetchone()[0]
        print(f"[OK] Total filas en BD: {count:,}")

        if count == len(df):
            print("[OK] Coincide con CSV!")
        else:
            print(f"[WARN] Discrepancia: CSV={len(df):,}, BD={count:,}")

except ConnectionError as e:
    print(f"[ERROR] Database connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except (pd.errors.ParserError, FileNotFoundError, IOError) as e:
    print(f"[ERROR] CSV loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except (ValueError, TypeError, AttributeError) as e:
    print(f"[ERROR] Data processing error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
