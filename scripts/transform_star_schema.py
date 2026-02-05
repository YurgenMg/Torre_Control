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

def get_db_connection():
    """Establish PostgreSQL connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print(f"✅ Connected to database: {DATABASE_URL.split('@')[1]}")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

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
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Transformation failed: {e}")
        return False

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
            if fact_count < 1000:
                print("⚠️  WARNING: fact_orders has fewer than expected records")
                return False
            
            print("✅ All tables populated successfully")
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main ETL transformation execution."""
    start_time = datetime.now()
    
    print("\n" + "="*60)
    print("🏢 TORRE CONTROL - ETL TRANSFORMATION PIPELINE")
    print("="*60)
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: SQL-based transformation (PostgreSQL native)")
    print("="*60 + "\n")
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Execute transformation SQL script
        sql_file = Path(__file__).parent.parent / 'sql' / 'populate_star_schema_simple.sql'
        
        if not sql_file.exists():
            print(f"❌ SQL script not found: {sql_file}")
            sys.exit(1)
        
        success = execute_sql_file(conn, sql_file)
        
        if not success:
            sys.exit(1)
        
        # Verify results
        if not verify_results(conn):
            print("⚠️  Verification warnings detected")
        
        # Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
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
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        conn.close()
        print("🔌 Database connection closed\n")

if __name__ == "__main__":
    main()
