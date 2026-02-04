#!/usr/bin/env python3
"""
Export Star Schema from PostgreSQL to CSV
Purpose: Generate CSVs for Power BI consumption from processed data
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE_URL = "postgresql://admin:adminpassword@localhost:5433/supply_chain_dw"
OUTPUT_DIR = Path("Data/Processed")
LOG_DIR = Path("logs")

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "export_star_schema.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ============================================================================
# MAIN EXPORT LOGIC
# ============================================================================


def connect_to_database():
    """Establish connection to PostgreSQL"""
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"✅ Connected to PostgreSQL at localhost:5433")
        return engine
    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error(
            "   Make sure PostgreSQL is running: 'docker-compose -f config/docker-compose.yml up -d'"
        )
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected connection error: {e}")
        raise


def export_table(engine, table_name, schema="dw"):
    """Export single table from PostgreSQL to CSV"""
    try:
        query = f"SELECT * FROM {schema}.{table_name}"
        logger.info(f"📥 Reading {schema}.{table_name}...")

        df = pd.read_sql_query(query, engine)

        output_path = OUTPUT_DIR / f"{table_name}.csv"
        df.to_csv(output_path, index=False, encoding="utf-8")

        logger.info(
            f"✅ {table_name}: {len(df):,} rows → {output_path.name} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)"
        )

        return df
    except Exception as e:
        logger.error(f"❌ Error exporting {table_name}: {e}")
        raise


def validate_exports(fact_orders, dim_customer, dim_product, dim_geography, dim_date):
    """Validate exported data"""
    logger.info("\n📊 Validating exports...")

    # Check row counts
    logger.info(f"  Fact Orders: {len(fact_orders):,} rows")
    logger.info(f"  Customers: {len(dim_customer):,} rows")
    logger.info(f"  Products: {len(dim_product):,} rows")
    logger.info(f"  Geography: {len(dim_geography):,} rows")
    logger.info(f"  Date: {len(dim_date):,} rows")

    # Check critical fields (no nulls)
    critical_fields = ["order_id", "customer_key", "product_key"]
    for field in critical_fields:
        if field in fact_orders.columns:
            null_count = fact_orders[field].isna().sum()
            if null_count == 0:
                logger.info(f"  ✅ {field}: No nulls")
            else:
                logger.warning(f"  ⚠️  {field}: {null_count} nulls found!")

    # Calculate OTIF%
    if "is_otif" in fact_orders.columns:
        otif_pct = (fact_orders["is_otif"].sum() / len(fact_orders)) * 100
        logger.info(f"  📈 OTIF%: {otif_pct:.2f}%")

    # Calculate Revenue at Risk
    if "revenue_at_risk" in fact_orders.columns:
        revenue_at_risk = fact_orders["revenue_at_risk"].sum()
        logger.info(f"  💰 Revenue at Risk: ${revenue_at_risk:,.2f}")

    logger.info("\n✅ Validation complete!\n")


def main():
    """Main export routine"""
    logger.info(
        f"\n{'='*70}\n"
        f"Tower Control - Star Schema Export\n"
        f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'='*70}\n"
    )

    try:
        # Connect
        engine = connect_to_database()

        # Export tables
        logger.info("\n📤 Exporting tables to CSV...\n")
        fact_orders = export_table(engine, "fact_orders")
        dim_customer = export_table(engine, "dim_customer")
        dim_product = export_table(engine, "dim_product")
        dim_geography = export_table(engine, "dim_geography")
        dim_date = export_table(engine, "dim_date")

        # Validate
        validate_exports(fact_orders, dim_customer,
                         dim_product, dim_geography, dim_date)

        logger.info(
            f"{'='*70}\n"
            f"✅ EXPORT SUCCESSFUL\n"
            f"Location: {OUTPUT_DIR.resolve()}\n"
            f"Files: fact_orders.csv, dim_customer.csv, dim_product.csv, dim_geography.csv, dim_date.csv\n"
            f"{'='*70}\n"
        )

        return 0

    except SQLAlchemyError as e:
        logger.error(f"\n❌ Database error: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        return 1
    finally:
        if engine:
            engine.dispose()


if __name__ == "__main__":
    exit(main())
