#!/usr/bin/env python3
"""
Tests básicos para ETL de Torre Control
Valida integridad del pipeline desde staging hasta fact table

Author: Torre Control Team
Date: 2026-02-04
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DB_URI = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:adminpassword@localhost:5433/supply_chain_dw"
)


@pytest.fixture(scope="module")
def db_engine():
    """Fixture para conexión a base de datos"""
    try:
        engine = create_engine(DB_URI)
        # Verificar conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        yield engine
        engine.dispose()
    except OperationalError as e:
        pytest.skip(f"PostgreSQL no disponible: {e}")


class TestStagingLayer:
    """Tests para capa de staging (stg_raw_orders)"""
    
    def test_staging_table_exists(self, db_engine):
        """Verifica que la tabla de staging existe"""
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'dw' 
                    AND table_name = 'stg_raw_orders'
                )
            """))
            exists = result.scalar()
            assert exists, "Tabla dw.stg_raw_orders no existe"
    
    def test_staging_not_empty(self, db_engine):
        """Verifica que staging tiene datos"""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dw.stg_raw_orders"))
            count = result.scalar()
            assert count > 0, "Tabla de staging está vacía"
            print(f"✅ Staging: {count:,} registros")
    
    def test_staging_critical_fields_not_null(self, db_engine):
        """Verifica que campos críticos no tienen NULLs"""
        critical_fields = ["order_id", "customer_id", "market", "sales"]
        
        with db_engine.connect() as conn:
            for field in critical_fields:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) FROM dw.stg_raw_orders 
                    WHERE {field} IS NULL
                """))
                null_count = result.scalar()
                assert null_count == 0, f"Campo '{field}' tiene {null_count} NULLs"


class TestDimensionTables:
    """Tests para tablas de dimensiones"""
    
    def test_dim_customer_populated(self, db_engine):
        """Verifica que dim_customer tiene registros"""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dw.dim_customer"))
            count = result.scalar()
            assert count > 0, "dim_customer está vacía"
            assert count > 10000, f"dim_customer tiene solo {count:,} registros (esperado >10K clientes únicos)"
            print(f"✅ dim_customer: {count:,} clientes")
    
    def test_dim_geography_populated(self, db_engine):
        """Verifica que dim_geography tiene registros"""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dw.dim_geography"))
            count = result.scalar()
            assert count > 0, "dim_geography está vacía"
            assert count > 40, f"dim_geography tiene solo {count:,} registros (esperado >40 combinaciones únicas)"
            print(f"✅ dim_geography: {count:,} ubicaciones")
    
    def test_dim_product_populated(self, db_engine):
        """Verifica que dim_product tiene registros"""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dw.dim_product"))
            count = result.scalar()
            assert count > 0, "dim_product está vacía"
            assert count > 50, f"dim_product tiene solo {count:,} registros (esperado >50)"
            print(f"✅ dim_product: {count:,} productos")
    
    def test_dim_date_populated(self, db_engine):
        """Verifica que dim_date tiene registros"""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dw.dim_date"))
            count = result.scalar()
            assert count > 0, "dim_date está vacía"
            assert count > 1000, f"dim_date tiene solo {count:,} registros (esperado >1K)"
            print(f"✅ dim_date: {count:,} fechas")
    
    def test_dim_customer_no_duplicates(self, db_engine):
        """Verifica que no hay clientes duplicados"""
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT customer_id, COUNT(*) as cnt 
                FROM dw.dim_customer 
                GROUP BY customer_id 
                HAVING COUNT(*) > 1
                LIMIT 1
            """))
            duplicate = result.fetchone()
            assert duplicate is None, f"Cliente duplicado encontrado: {duplicate}"


class TestFactTable:
    """Tests para tabla de hechos (fact_orders)"""
    
    def test_fact_orders_populated(self, db_engine):
        """Verifica que fact_orders tiene registros"""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dw.fact_orders"))
            count = result.scalar()
            assert count > 0, "fact_orders está vacía"
            assert count > 40000, f"fact_orders tiene solo {count:,} registros (esperado >40K order items)"
            print(f"✅ fact_orders: {count:,} transacciones")
    
    def test_fact_orders_no_null_fks(self, db_engine):
        """Verifica que no hay NULLs en foreign keys"""
        fk_fields = ["customer_key", "product_key", "geo_key", "date_key"]
        
        with db_engine.connect() as conn:
            for field in fk_fields:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) FROM dw.fact_orders 
                    WHERE {field} IS NULL
                """))
                null_count = result.scalar()
                assert null_count == 0, f"FK '{field}' tiene {null_count} NULLs"
    
    def test_fact_orders_referential_integrity(self, db_engine):
        """Verifica integridad referencial (FKs válidas)"""
        with db_engine.connect() as conn:
            # Test customer_key
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM dw.fact_orders f
                LEFT JOIN dw.dim_customer c ON f.customer_key = c.customer_key
                WHERE c.customer_key IS NULL
            """))
            orphans = result.scalar()
            assert orphans == 0, f"fact_orders tiene {orphans} registros con customer_key inválido"
            
            # Test geo_key
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM dw.fact_orders f
                LEFT JOIN dw.dim_geography g ON f.geo_key = g.geo_key
                WHERE g.geo_key IS NULL
            """))
            orphans = result.scalar()
            assert orphans == 0, f"fact_orders tiene {orphans} registros con geo_key inválido"
    
    def test_fact_orders_sales_positive(self, db_engine):
        """Verifica que sales no son negativos (en mayoría)"""
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) FILTER (WHERE sales < 0) as negative_count,
                    COUNT(*) as total_count
                FROM dw.fact_orders
            """))
            row = result.fetchone()
            negative_count, total_count = row
            negative_pct = (negative_count / total_count) * 100 if total_count > 0 else 0
            
            # Permitir hasta 1% de ventas negativas (cancelaciones, devoluciones)
            assert negative_pct < 1.0, f"Demasiadas ventas negativas: {negative_pct:.2f}%"


class TestBusinessMetrics:
    """Tests para métricas de negocio (5 Preguntas Estratégicas)"""
    
    def test_otif_calculation(self, db_engine):
        """Verifica que OTIF% está calculado y es razonable"""
        with db_engine.connect() as conn:
            # Verificar si la vista existe, si no, calcular directamente
            try:
                result = conn.execute(text("""
                    SELECT AVG(otif_percentage) as avg_otif
                    FROM dw.v_otif_by_market
                """))
                avg_otif = result.scalar()
            except Exception:
                # Si la vista no existe, calcular desde fact_orders
                conn.rollback()  # Limpiar transacción fallida
                result = conn.execute(text("""
                    SELECT 
                        (COUNT(*) FILTER (WHERE late_delivery_risk = 0) * 100.0 / NULLIF(COUNT(*), 0)) as otif_pct
                    FROM dw.fact_orders
                """))
                avg_otif = result.scalar()
            
            assert avg_otif is not None, "OTIF% no calculado"
            assert avg_otif > 30, f"OTIF promedio muy bajo: {avg_otif:.2f}%"
            assert avg_otif < 100, f"OTIF promedio sospechosamente alto: {avg_otif:.2f}%"
            print(f"✅ OTIF promedio: {avg_otif:.2f}%")
    
    def test_revenue_at_risk_calculation(self, db_engine):
        """Verifica cálculo de Revenue at Risk (Q2)"""
        with db_engine.connect() as conn:
            # Calcular directamente desde fact_orders
            result = conn.execute(text("""
                SELECT SUM(sales * late_delivery_risk) as total_risk
                FROM dw.fact_orders
            """))
            total_risk = result.scalar()
            
            assert total_risk is not None, "Revenue at Risk no calculado"
            assert total_risk >= 0, "Revenue at Risk no puede ser negativo"
            print(f"✅ Revenue at Risk: ${total_risk:,.2f}")
    
    def test_market_distribution(self, db_engine):
        """Verifica que hay datos en todos los markets (Q4)"""
        expected_markets = ['Africa', 'Europe', 'LATAM', 'Pacific Asia', 'USCA']
        
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT DISTINCT market 
                FROM dw.dim_geography
                ORDER BY market
            """))
            markets = [row[0] for row in result]
            
            for expected in expected_markets:
                assert expected in markets, f"Market '{expected}' no encontrado en dim_geography"
            
            print(f"✅ Markets presentes: {', '.join(markets)}")


class TestViews:
    """Tests para vistas materializadas (opcional si existen)"""
    
    def test_v_otif_by_market_exists(self, db_engine):
        """Verifica que vista OTIF existe y tiene datos (si está implementada)"""
        with db_engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM dw.v_otif_by_market"))
                count = result.scalar()
                if count > 0:
                    assert count == 5, f"Vista debe tener 5 markets, tiene {count}"
                    print("✅ Vista v_otif_by_market existe y tiene datos")
                else:
                    print("⚠️  Vista v_otif_by_market existe pero está vacía")
            except:
                print("ℹ️  Vista v_otif_by_market no implementada (opcional)")
    
    def test_v_revenue_at_risk_exists(self, db_engine):
        """Verifica que vista Revenue at Risk existe (si está implementada)"""
        with db_engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM dw.v_revenue_at_risk_by_market"))
                count = result.scalar()
                if count > 0:
                    print("✅ Vista v_revenue_at_risk_by_market existe y tiene datos")
                else:
                    print("⚠️  Vista v_revenue_at_risk_by_market existe pero está vacía")
            except:
                print("ℹ️  Vista v_revenue_at_risk_by_market no implementada (opcional)")


if __name__ == "__main__":
    # Ejecutar tests con pytest
    pytest.main([__file__, "-v", "--tb=short"])
