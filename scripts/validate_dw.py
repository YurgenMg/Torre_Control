"""
Validate Data Warehouse - Muestra métricas del DW (equivalente a 'make validate')
"""
import psycopg2
from decimal import Decimal

def validate_dw():
    """Valida y muestra métricas del Data Warehouse"""
    conn = psycopg2.connect(
        'postgresql://admin:adminpassword@localhost:5433/supply_chain_dw'
    )
    cur = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 DATA WAREHOUSE VALIDATION".center(60))
    print("="*60 + "\n")
    
    queries = {
        "Staging": "SELECT COUNT(*) FROM dw.stg_raw_orders",
        "Customers": "SELECT COUNT(*) FROM dw.dim_customer",
        "Products": "SELECT COUNT(*) FROM dw.dim_product",
        "Geography": "SELECT COUNT(*) FROM dw.dim_geography",
        "Dates": "SELECT COUNT(*) FROM dw.dim_date",
        "Fact Orders": "SELECT COUNT(*) FROM dw.fact_orders",
        "OTIF %": "SELECT ROUND(AVG((late_delivery_risk = 0)::int) * 100, 2) FROM dw.fact_orders",
        "Markets": "SELECT COUNT(DISTINCT market) FROM dw.dim_geography"
    }
    
    for label, query in queries.items():
        cur.execute(query)
        result = cur.fetchone()[0]
        if isinstance(result, (int, Decimal)):
            if label == "OTIF %":
                print(f"{label:20} {result:>10}%")
            else:
                print(f"{label:20} {result:>10,}")
        else:
            print(f"{label:20} {result:>10}")
    
    print("\n" + "="*60 + "\n")
    
    conn.close()
    print("✅ Validación completada exitosamente")

if __name__ == "__main__":
    validate_dw()
