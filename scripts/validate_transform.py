#!/usr/bin/env python3
"""
Data Quality Validation for Transform Pipeline
Purpose: Pre-flight checks before running transform_data.py
"""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE_URL = "postgresql://admin:adminpassword@localhost:5433/supply_chain_dw"
LOG_DIR = Path("logs")

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "validate_transform.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def validate_database_connection():
    """Check database connectivity."""
    logger.info("\n🔍 Validating database connection...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("  ✅ PostgreSQL connection OK")
        return engine
    except Exception as e:
        logger.error(f"  ❌ Connection failed: {e}")
        raise


def validate_schema_exists(engine):
    """Check if dw schema exists."""
    logger.info("\n🔍 Validating schema structure...")
    
    inspector = inspect(engine)
    schemas = inspector.get_schema_names()
    
    if "dw" not in schemas:
        logger.error("  ❌ Schema 'dw' not found!")
        return False
    
    logger.info("  ✅ Schema 'dw' exists")
    return True


def validate_tables_exist(engine):
    """Check if required tables exist."""
    logger.info("\n🔍 Validating required tables...")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="dw")
    
    required_tables = {
        "stg_raw_orders": "Staging table (input)",
        "dim_customer": "Customer dimension",
        "dim_product": "Product dimension",
        "dim_geography": "Geography dimension",
        "dim_date": "Date dimension",
        "fact_orders": "Orders fact table",
    }
    
    all_ok = True
    for table, description in required_tables.items():
        if table in tables:
            logger.info(f"  ✅ {table}: {description}")
        else:
            logger.error(f"  ❌ {table}: MISSING")
            all_ok = False
    
    return all_ok


def validate_staging_data(engine):
    """Check staging table has data."""
    logger.info("\n🔍 Validating staging data...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) as cnt FROM dw.stg_raw_orders")
            )
            count = result.fetchone()[0]
        
        if count == 0:
            logger.error("  ❌ stg_raw_orders is EMPTY!")
            return False
        
        logger.info(f"  ✅ stg_raw_orders: {count:,} rows")
        
        # Check unprocessed count
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) as cnt FROM dw.stg_raw_orders WHERE is_processed = FALSE")
            )
            unprocessed = result.fetchone()[0]
        
        logger.info(f"  ✅ Unprocessed rows: {unprocessed:,}")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Error reading staging: {e}")
        return False


def validate_critical_fields(engine):
    """Check critical fields exist in staging."""
    logger.info("\n🔍 Validating critical fields...")
    
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("stg_raw_orders", schema="dw")}
    
    critical_fields = {
        "customer_id": "Customer identification",
        "order_id": "Order identification",
        "order_item_id": "Order item identification",
        "order_date": "Order date",
        "market": "Market (geography)",
        "order_region": "Region (geography)",
        "product_card_id": "Product identification",
        "sales": "Sales amount",
        "late_delivery_risk": "Delivery risk flag",
    }
    
    all_ok = True
    for field, description in critical_fields.items():
        if field in columns:
            logger.info(f"  ✅ {field}: {description}")
        else:
            logger.error(f"  ❌ {field}: MISSING")
            all_ok = False
    
    return all_ok


def validate_dimension_capacity(engine):
    """Check if dimension tables are empty (ready for population)."""
    logger.info("\n🔍 Validating dimension tables (should be empty)...")
    
    dimensions = ["dim_customer", "dim_product", "dim_geography", "dim_date"]
    
    all_ok = True
    for dim in dimensions:
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) as cnt FROM dw.{dim}")
                )
                count = result.fetchone()[0]
            
            if count > 0:
                logger.warning(f"  ⚠️  {dim}: {count:,} rows already present (will be upserted)")
            else:
                logger.info(f"  ✅ {dim}: Empty (ready for population)")
        except Exception as e:
            logger.error(f"  ❌ {dim}: Error reading - {e}")
            all_ok = False
    
    return all_ok


def validate_fact_table_empty(engine):
    """Check if fact table is empty."""
    logger.info("\n🔍 Validating fact_orders table...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) as cnt FROM dw.fact_orders")
            )
            count = result.fetchone()[0]
        
        if count > 0:
            logger.warning(f"  ⚠️  fact_orders: {count:,} rows already present (will be upserted)")
        else:
            logger.info(f"  ✅ fact_orders: Empty (ready for population)")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ fact_orders: Error reading - {e}")
        return False


def validate_indexes(engine):
    """Check if required indexes exist."""
    logger.info("\n🔍 Validating indexes...")
    
    inspector = inspect(engine)
    indexes = inspector.get_indexes("fact_orders", schema="dw")
    index_names = {idx["name"] for idx in indexes}
    
    # Expected indexes
    expected_indexes = [
        "idx_fact_orders_customer_key",
        "idx_fact_orders_geography_key",
        "idx_fact_orders_product_key",
        "idx_fact_orders_date_key",
    ]
    
    for idx_name in expected_indexes:
        if idx_name in index_names:
            logger.info(f"  ✅ {idx_name}")
        else:
            logger.warning(f"  ⚠️  {idx_name}: Not found (performance may suffer)")
    
    return True


def run_validation():
    """Run all validations."""
    logger.info(
        "\n" + "=" * 70
        + "\nDATA QUALITY VALIDATION - Pre-Transform Checks\n"
        + "=" * 70
    )
    
    try:
        # 1. Connection
        engine = validate_database_connection()
        
        # 2. Schema
        if not validate_schema_exists(engine):
            return False
        
        # 3. Tables
        if not validate_tables_exist(engine):
            return False
        
        # 4. Staging data
        if not validate_staging_data(engine):
            return False
        
        # 5. Critical fields
        if not validate_critical_fields(engine):
            return False
        
        # 6. Dimension capacity
        validate_dimension_capacity(engine)
        
        # 7. Fact table
        validate_fact_table_empty(engine)
        
        # 8. Indexes
        validate_indexes(engine)
        
        # Summary
        logger.info(
            "\n" + "=" * 70
            + "\n✅ VALIDATION SUCCESSFUL - Ready to run transform_data.py\n"
            + "=" * 70
            + "\n"
        )
        
        engine.dispose()
        return True
        
    except Exception as e:
        logger.error(
            "\n" + "=" * 70
            + f"\n❌ VALIDATION FAILED: {e}\n"
            + "=" * 70
            + "\n"
        )
        return False


if __name__ == "__main__":
    success = run_validation()
    exit(0 if success else 1)
