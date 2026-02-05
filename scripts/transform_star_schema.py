#!/usr/bin/env python3
"""
Torre Control - ETL Transformation Pipeline
Transforms staging data into star schema using native SQL for optimal performance.

Author: Torre Control Team
Date: 2026-02-04
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://admin:adminpassword@localhost:5433/supply_chain_dw')

# ============================================================================
# CUSTOM EXCEPTIONS FOR TORRE CONTROL ETL
# ============================================================================

class TorreControlETLError(Exception):
    """Base exception para errores del pipeline ETL de Torre Control."""
    pass

class SQLScriptNotFoundError(TorreControlETLError):
    """El archivo SQL de transformación no existe."""
    pass

class SQLExecutionError(TorreControlETLError):
    """Error al ejecutar script SQL en PostgreSQL."""
    pass

class DataValidationError(TorreControlETLError):
    """Fallo en validación post-transformación (star schema vacío, etc.)."""
    pass

class DatabaseConnectionError(TorreControlETLError):
    """Error al conectar con PostgreSQL."""
    pass

def get_db_connection():
    """Establish PostgreSQL connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print(f"✅ Connected to database: {DATABASE_URL.split('@')[1]}")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("   Action: Check if PostgreSQL container is running (docker ps)")
        raise DatabaseConnectionError(f"Cannot connect to PostgreSQL: {e}") from e
    except Exception as e:
        print(f"❌ Unexpected connection error: {type(e).__name__}: {e}")
        raise DatabaseConnectionError(f"Connection failed: {e}") from e

def execute_sql_file(conn, sql_file_path):
    """Execute SQL transformation script."""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print(f"\n🔄 Executing transformation: {sql_file_path}")
        
        with conn.cursor() as cursor:
            cursor.execute(sql_script)
            conn.commit()
        
        print("✅ Transformation completed successfully")
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ SQL execution failed: {e.pgcode} - {e.pgerror}")
        print("   Action: Review SQL script syntax and staging data")
        raise SQLExecutionError(f"PostgreSQL error: {e.pgcode} - {e.pgerror}") from e
    except FileNotFoundError as e:
        print(f"❌ SQL script file not found: {sql_file_path}")
        raise SQLScriptNotFoundError(f"Script not found: {e}") from e
    except Exception as e:
        conn.rollback()
        print(f"❌ Unexpected transformation error: {type(e).__name__}: {e}")
        raise SQLExecutionError(f"Transformation failed: {e}") from e

def verify_results(conn):
    """Verify star schema population."""
    print("\n" + "="*60)
    print("📊 STAR SCHEMA VERIFICATION")
    print("="*60)
    
    verification_query = """
    SELECT 'dim_customer' as tabla, COUNT(*) as registros FROM dw.dim_customer
    UNION ALL SELECT 'dim_geography', COUNT(*) FROM dw.dim_geography
    UNION ALL SELECT 'dim_product', COUNT(*) FROM dw.dim_product
    UNION ALL SELECT 'dim_date', COUNT(*) FROM dw.dim_date
    UNION ALL SELECT 'fact_orders', COUNT(*) FROM dw.fact_orders
    ORDER BY tabla;
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(verification_query)
            results = cursor.fetchall()
            
            print(f"\n{'Tabla':<20} {'Registros':>15}")
            print("-" * 36)
            
            total_records = 0
            for tabla, registros in results:
                print(f"{tabla:<20} {registros:>15,}")
                total_records += registros
            
            print("-" * 36)
            print(f"{'TOTAL':<20} {total_records:>15,}\n")
            
            # Validate minimum expected records
            fact_count = [r[1] for r in results if r[0] == 'fact_orders'][0]
            
            if fact_count == 0:
                print("❌ CRITICAL: fact_orders table is empty")
                print("   Action: Check staging table (stg_raw_orders) has data")
                raise DataValidationError("fact_orders is empty - ETL transformation failed")
            
            if fact_count < 1000:
                print("⚠️  WARNING: fact_orders has fewer than expected records")
                print(f"   Found: {fact_count:,} | Expected: 100,000+ orders")
            
            print("✅ All tables populated successfully")
            return True
            
    except psycopg2.Error as e:
        print(f"❌ Database error during verification: {e}")
        print("   Action: Check PostgreSQL connection and table permissions")
        raise DataValidationError(f"Verification query failed: {e}") from e
    except DataValidationError:
        # Re-raise para que main() la capture
        raise
    except Exception as e:
        print(f"❌ Unexpected verification error: {type(e).__name__}: {e}")
        raise DataValidationError(f"Verification failed: {e}") from e

def main():
    """Main ETL transformation execution."""
    start_time = datetime.now()
    
    print("\n" + "="*60)
    print("🏢 TORRE CONTROL - ETL TRANSFORMATION PIPELINE")
    print("="*60)
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Mode: SQL-based transformation (PostgreSQL native)")
    print("="*60 + "\n")
    
    conn = None
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Execute transformation SQL script
        sql_file = Path(__file__).parent.parent / 'sql' / 'populate_star_schema_simple.sql'
        
        if not sql_file.exists():
            raise SQLScriptNotFoundError(
                f"SQL script not found: {sql_file}\n"
                "   Expected path: sql/populate_star_schema_simple.sql"
            )
        
        execute_sql_file(conn, sql_file)
        
        # Verify results
        verify_results(conn)
        
        # Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print(f"Duration: {duration:.2f} seconds")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        print("📋 Next Steps:")
        print("  1. Connect Power BI Desktop to PostgreSQL")
        print("     - Host: localhost:5433")
        print("     - Database: supply_chain_dw")
        print("     - Schema: dw")
        print("  2. Import all 5 tables (dim_*, fact_orders)")
        print("  3. Verify relationships in Model View")
        print("  4. Create DAX measures for KPIs\n")
        
        return 0
        
    except SQLScriptNotFoundError as e:
        print(f"\n❌ CONFIGURATION ERROR: {e}")
        print("   Action: Create sql/populate_star_schema_simple.sql")
        return 1
        
    except DatabaseConnectionError as e:
        print(f"\n❌ DATABASE CONNECTION ERROR: {e}")
        print("   Action: Start PostgreSQL container (docker-compose up -d)")
        return 1
        
    except SQLExecutionError as e:
        print(f"\n❌ SQL TRANSFORMATION ERROR: {e}")
        print("   Action: Review SQL script and staging data")
        return 1
        
    except DataValidationError as e:
        print(f"\n❌ DATA VALIDATION ERROR: {e}")
        print("   Action: Check staging table has records")
        return 1
        
    except psycopg2.Error as e:
        print(f"\n❌ UNEXPECTED DATABASE ERROR:")
        print(f"   Error Code: {e.pgcode}")
        print(f"   Message: {e.pgerror}")
        print("   Action: Check PostgreSQL logs")
        return 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user (Ctrl+C)")
        return 130
        
    except Exception as e:
        print(f"\n❌❌❌ CRITICAL UNEXPECTED ERROR:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")
        print("   This indicates a bug - review stack trace:\n")
        
        import traceback
        traceback.print_exc()
        
        return 1
        
    finally:
        if conn:
            conn.close()
            print("🔌 Database connection closed\n")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
