#!/usr/bin/env python3
"""
⚠️  DEPRECATED - Use scripts/transform_star_schema.py instead

This pandas-based script has schema compatibility issues.
The production pipeline now uses SQL for better performance and reliability.

Transform Stage Layer to Star Schema (Dimensions + Facts) - LEGACY VERSION
Purpose: Convert stg_raw_orders into dim_customer, dim_geography, dim_product, 
        dim_date, and fact_orders with data quality validation.

Author: Data Engineering Team (Torre Control)
Date: 2026-02-04
Deprecated: 2026-02-04
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from tqdm import tqdm

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:adminpassword@localhost:5433/supply_chain_dw"
)

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "transform_data.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def log(message, level="INFO"):
    """Centralized logging utility."""
    level_map = {
        "DEBUG": logger.debug,
        "INFO": logger.info,
        "WARNING": logger.warning,
        "ERROR": logger.error,
        "CRITICAL": logger.critical,
    }
    level_map.get(level, logger.info)(message)


# ============================================================================
# DATABASE CONNECTION
# ============================================================================


def get_db_connection():
    """Establish PostgreSQL connection."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log(f"✅ Connected to PostgreSQL: {DATABASE_URL.split('@')[1]}", "INFO")
        return engine
    except Exception as e:
        log(f"❌ Connection failed: {e}", "ERROR")
        raise


# ============================================================================
# DIMENSION POPULATION FUNCTIONS
# ============================================================================


def populate_dim_customer(engine):
    """Populate dim_customer from stg_raw_orders."""
    log("\n🔄 [1/5] Populating dim_customer...", "INFO")
    
    try:
        query = """
            SELECT 
                stg.customer_id,
                stg.customer_fname,
                stg.customer_lname,
                stg.customer_email,
                stg.customer_segment,
                SUM(COALESCE(stg.sales, 0)) as sales_per_customer,
                COUNT(*) as order_count
            FROM dw.stg_raw_orders stg
            WHERE stg.customer_id IS NOT NULL
            GROUP BY stg.customer_id, stg.customer_fname, stg.customer_lname, 
                    stg.customer_email, stg.customer_segment
        """
        
        with engine.connect() as conn:
            df_customers = pd.read_sql_query(query, conn)
        
        log(f"  📥 Read {len(df_customers):,} unique customers from staging", "INFO")
        
        # Asegurarse de que los campos requeridos no sean nulos
        df_customers["sales_per_customer"] = df_customers["sales_per_customer"].astype(float)
        
        critical_fields = ["customer_id", "customer_fname", "customer_lname"]
        for field in critical_fields:
            null_count = df_customers[field].isna().sum()
            if null_count > 0:
                log(f"  ⚠️  {field}: {null_count} NULLs detected (will skip)", "WARNING")
                df_customers = df_customers[df_customers[field].notna()]
        
        insert_count = 0
        
        with engine.begin() as conn:
            for _, row in tqdm(df_customers.iterrows(), total=len(df_customers), desc="  Inserting customers"):
                upsert_query = text("""
                    INSERT INTO dw.dim_customer 
                    (customer_id, fname, lname, segment)
                    VALUES (:customer_id, :fname, :lname, :segment)
                    ON CONFLICT (customer_key) DO NOTHING
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "customer_id": str(row["customer_id"]),
                            "fname": row["customer_fname"],
                            "lname": row["customer_lname"],
                            "segment": row["customer_segment"]
                        }
                    )
                    insert_count += 1
                except IntegrityError as e:
                    log(f"  ⚠️  Integrity error for customer {row['customer_id']}: {e}", "WARNING")
        
        log(f"✅ dim_customer: {insert_count:,} inserted/updated", "INFO")
        
        with engine.connect() as conn:
            df_lookup = pd.read_sql_query("SELECT customer_id, customer_key FROM dw.dim_customer", conn)
        
        lookup_dict = dict(zip(df_lookup["customer_id"], df_lookup["customer_key"]))
        log(f"  📌 Customer lookup dict: {len(lookup_dict)} entries", "INFO")
        
        return lookup_dict
        
    except Exception as e:
        log(f"❌ Error in populate_dim_customer: {e}", "ERROR")
        raise


def populate_dim_geography(engine):
    """Populate dim_geography from stg_raw_orders.
    
    NOTE: Real schema only has (market, region, country) - not state/city
    This version is simplified to match actual database schema.
    """
    log("\n🔄 [2/5] Populating dim_geography...", "INFO")
    
    try:
        query = """
            SELECT DISTINCT
                stg.market,
                stg.order_region as region,
                stg.customer_country as country
            FROM dw.stg_raw_orders stg
            WHERE stg.market IS NOT NULL
        """
        
        with engine.connect() as conn:
            df_geo = pd.read_sql_query(query, conn)
        
        log(f"  📥 Read {len(df_geo):,} unique geographic combinations", "INFO")
        
        valid_markets = {"Africa", "Europe", "LATAM", "Pacific Asia", "USCA"}
        invalid_markets = df_geo[~df_geo["market"].isin(valid_markets)]["market"].unique()
        
        if len(invalid_markets) > 0:
            log(f"  ⚠️  Invalid markets detected: {invalid_markets}. Filtering out.", "WARNING")
            df_geo = df_geo[df_geo["market"].isin(valid_markets)]
        
        df_geo["region"] = df_geo["region"].fillna("Unknown")
        df_geo["country"] = df_geo["country"].fillna("Unknown")
        
        log(f"  ✅ Validated {len(df_geo):,} geographic records", "INFO")
        
        insert_count = 0
        
        with engine.begin() as conn:
            for _, row in tqdm(df_geo.iterrows(), total=len(df_geo), desc="  Inserting geographies"):
                upsert_query = text("""
                    INSERT INTO dw.dim_geography 
                    (market, region, country)
                    VALUES (:market, :region, :country)
                    ON CONFLICT (geo_key) DO NOTHING
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "market": row["market"],
                            "region": row["region"],
                            "country": row["country"]
                        }
                    )
                    insert_count += 1
                except (SQLAlchemyError, IntegrityError) as e:
                    log(f"  ⚠️  Error inserting geography: {e}", "WARNING")
        
        log(f"✅ dim_geography: {insert_count:,} inserted", "INFO")
        
        with engine.connect() as conn:
            df_geo_lookup = pd.read_sql_query(
                "SELECT market, region, country, geo_key FROM dw.dim_geography", conn
            )
        
        lookup_dict = {}
        for _, row in df_geo_lookup.iterrows():
            key = (row["market"], row["region"], row["country"])
            lookup_dict[key] = row["geo_key"]
        
        log(f"  📌 Geography lookup dict: {len(lookup_dict)} entries", "INFO")
        
        return lookup_dict
        
    except (SQLAlchemyError, KeyError, ValueError) as e:
        log(f"❌ Error in populate_dim_geography: {e}", "ERROR")
        raise


def populate_dim_product(engine):
    """Populate dim_product from stg_raw_orders."""
    log("\n🔄 [3/5] Populating dim_product...", "INFO")
    
    try:
        query = """
            SELECT DISTINCT
                stg.product_card_id,
                stg.product_name,
                stg.category_name,
                stg.department_name,
                stg.product_price
            FROM dw.stg_raw_orders stg
            WHERE stg.product_card_id IS NOT NULL
        """
        
        with engine.connect() as conn:
            df_products = pd.read_sql_query(query, conn)
        
        log(f"  📥 Read {len(df_products):,} unique products from staging", "INFO")
        
        df_products["product_name"] = df_products["product_name"].fillna("Unknown")
        df_products["category_name"] = df_products["category_name"].fillna("Unknown")
        df_products["department_name"] = df_products["department_name"].fillna("Unknown")
        df_products["product_price"] = pd.to_numeric(df_products["product_price"], errors="coerce").fillna(0.0)
        
        insert_count = 0
        
        with engine.begin() as conn:
            for _, row in tqdm(df_products.iterrows(), total=len(df_products), desc="  Inserting products"):
                upsert_query = text("""
                    INSERT INTO dw.dim_product 
                    (product_id, product_name, category)
                    VALUES (:product_id, :product_name, :category)
                    ON CONFLICT (product_key) DO NOTHING
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "product_id": str(row["product_card_id"]),
                            "product_name": row["product_name"],
                            "category": row["category_name"]
                        }
                    )
                    insert_count += 1
                except (SQLAlchemyError, IntegrityError, KeyError) as e:
                    log(f"  ⚠️  Error inserting product {row['product_card_id']}: {e}", "WARNING")
        
        log(f"✅ dim_product: {insert_count:,} inserted", "INFO")
        
        with engine.connect() as conn:
            df_lookup = pd.read_sql_query("SELECT product_id, product_key FROM dw.dim_product", conn)
        
        lookup_dict = dict(zip(df_lookup["product_id"], df_lookup["product_key"]))
        log(f"  📌 Product lookup dict: {len(lookup_dict)} entries", "INFO")
        
        return lookup_dict
        
    except (SQLAlchemyError, KeyError, ValueError) as e:
        log(f"❌ Error in populate_dim_product: {e}", "ERROR")
        raise


def populate_dim_date(engine):
    """Populate dim_date from stg_raw_orders.
    
    NOTE: Uses order_date_(dateorders) as actual column name in staging.
    """
    log("\n🔄 [4/5] Populating dim_date...", "INFO")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        MIN(stg."order_date_(dateorders)") as min_date,
                        MAX(stg."order_date_(dateorders)") as max_date
                    FROM dw.stg_raw_orders stg
                    WHERE stg."order_date_(dateorders)" IS NOT NULL
                """)
            )
            row = result.fetchone()
            min_date = row[0]
            max_date = row[1]
        
        log(f"  📅 Date range: {min_date} to {max_date}", "INFO")
        
        date_range = pd.date_range(start=min_date, end=max_date, freq="D")
        df_dates = pd.DataFrame({"order_date": date_range})
        
        df_dates["date_id"] = df_dates["order_date"].dt.strftime("%Y%m%d").astype(int)
        df_dates["year"] = df_dates["order_date"].dt.year
        df_dates["quarter"] = df_dates["order_date"].dt.quarter
        df_dates["month"] = df_dates["order_date"].dt.month
        df_dates["week"] = df_dates["order_date"].dt.isocalendar().week
        df_dates["day_of_month"] = df_dates["order_date"].dt.day
        df_dates["day_of_week"] = df_dates["order_date"].dt.dayofweek + 1
        df_dates["month_name"] = df_dates["order_date"].dt.strftime("%B")
        df_dates["day_name"] = df_dates["order_date"].dt.strftime("%A")
        df_dates["is_weekend"] = df_dates["day_of_week"].isin([6, 7]).astype(int)
        
        log(f"  📅 Generated {len(df_dates):,} calendar dates", "INFO")
        
        insert_count = 0
        
        # Note: dim_date schema has fewer columns - simplified insert
        with engine.begin() as conn:
            for _, row in tqdm(df_dates.iterrows(), total=len(df_dates), desc="  Inserting dates"):
                upsert_query = text("""
                    INSERT INTO dw.dim_date 
                    (order_date, year, month, day)
                    VALUES (:order_date, :year, :month, :day)
                    ON CONFLICT (date_key) DO NOTHING
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "order_date": row["order_date"],
                            "year": int(row["year"]),
                            "month": int(row["month"]),
                            "day": int(row["day_of_month"])
                        }
                    )
                    insert_count += 1
                except (SQLAlchemyError, IntegrityError, ValueError) as e:
                    log(f"  ⚠️  Error inserting date {row['order_date']}: {e}", "WARNING")
        
        log(f"✅ dim_date: {insert_count:,} inserted", "INFO")
        
        # Get actual date_key from database after insert
        with engine.connect() as conn:
            df_date_lookup = pd.read_sql_query(
                "SELECT order_date, date_key FROM dw.dim_date", conn
            )
        
        lookup_dict = dict(zip(df_date_lookup["order_date"], df_date_lookup["date_key"]))
        log(f"  📌 Date lookup dict: {len(lookup_dict)} entries", "INFO")
        
        return lookup_dict
        
    except (SQLAlchemyError, KeyError, ValueError) as e:
        log(f"❌ Error in populate_dim_date: {e}", "ERROR")
        raise


def populate_fact_orders(engine, customer_lookup, geography_lookup, product_lookup, date_lookup, etl_run_id):
    """Populate fact_orders from stg_raw_orders."""
    log("\n🔄 [5/5] Populating fact_orders...", "INFO")
    
    try:
        query = """
            SELECT 
                stg.order_id, stg.order_item_id, stg.customer_id, stg.market,
                stg.order_region, stg.customer_country,
                stg.product_card_id, stg."order_date_(dateorders)" as order_date, 
                stg.sales, stg.benefit_per_order,
                stg.order_item_quantity, stg.order_item_total, stg.order_item_profit_ratio,
                stg.late_delivery_risk, stg.days_for_shipping_real, stg.days_for_shipment_scheduled,
                stg.delivery_status, stg.order_item_discount_rate
            FROM dw.stg_raw_orders stg
            WHERE stg.is_processed = FALSE
            ORDER BY stg.order_id, stg.order_item_id
        """
        
        with engine.connect() as conn:
            df_facts = pd.read_sql_query(query, conn)
        
        log(f"  📥 Read {len(df_facts):,} unprocessed order items from staging", "INFO")
        
        if len(df_facts) == 0:
            log("  ⚠️  No unprocessed orders found. Skipping fact population.", "WARNING")
            return {"total_orders": 0, "inserted": 0, "skipped": 0}
        
        df_facts["customer_key"] = df_facts["customer_id"].astype(str).map(customer_lookup)
        df_facts["geography_key"] = df_facts.apply(
            lambda row: geography_lookup.get(
                (row["market"], row["order_region"], row["customer_country"])
            ), axis=1
        )
        df_facts["product_key"] = df_facts["product_card_id"].astype(str).map(product_lookup)
        
        # Map date_key with proper datetime handling
        df_facts["date_key"] = pd.to_datetime(df_facts["order_date"], errors="coerce").map(date_lookup)
        
        fk_nulls = {
            "customer_key": df_facts["customer_key"].isna().sum(),
            "geography_key": df_facts["geography_key"].isna().sum(),
            "product_key": df_facts["product_key"].isna().sum(),
            "date_key": df_facts["date_key"].isna().sum(),
        }
        
        for fk, null_count in fk_nulls.items():
            if null_count > 0:
                log(f"  ⚠️  {fk}: {null_count:,} NULLs (rows will be skipped)", "WARNING")
        
        df_facts_valid = df_facts[
            df_facts["customer_key"].notna() &
            df_facts["geography_key"].notna() &
            df_facts["product_key"].notna() &
            df_facts["date_key"].notna()
        ].copy()
        
        skipped_count = len(df_facts) - len(df_facts_valid)
        log(f"  ✅ Valid fact rows: {len(df_facts_valid):,} (skipped: {skipped_count:,})", "INFO")
        
        df_facts_valid["is_otif"] = (df_facts_valid["late_delivery_risk"] == 0).astype(int)
        df_facts_valid["revenue_at_risk"] = df_facts_valid["sales"] * df_facts_valid["late_delivery_risk"]
        df_facts_valid["etl_run_id"] = etl_run_id
        
        # Validate numeric fields
        numeric_fields = ["sales", "benefit_per_order", "order_item_total", 
                        "order_item_profit_ratio", "order_item_discount_rate"]
        for field in numeric_fields:
            df_facts_valid[field] = pd.to_numeric(df_facts_valid[field], errors="coerce").fillna(0)
        
        anomalies = df_facts_valid[
            (df_facts_valid["days_for_shipping_real"] > 60) |
            (df_facts_valid["order_item_discount_rate"] > 100)
        ]
        
        if len(anomalies) > 0:
            log(f"  ⚠️  Detected {len(anomalies):,} anomalies (delay>60d or discount>100%)", "WARNING")
        
        insert_count = 0
        batch_size = 1000
        
        with engine.begin() as conn:
            for batch_start in tqdm(
                range(0, len(df_facts_valid), batch_size),
                desc="  Inserting facts",
                total=(len(df_facts_valid) + batch_size - 1) // batch_size
            ):
                batch_end = min(batch_start + batch_size, len(df_facts_valid))
                batch = df_facts_valid.iloc[batch_start:batch_end]
                
                for _, row in batch.iterrows():
                    upsert_query = text("""
                        INSERT INTO dw.fact_orders 
                        (order_id, customer_key, product_key, geo_key, date_key, sales, late_delivery_risk)
                        VALUES (:order_id, :customer_key, :product_key, :geo_key, :date_key, :sales, :late_delivery_risk)
                    """)
                    
                    try:
                        conn.execute(upsert_query, {
                            "order_id": str(row["order_id"]),
                            "customer_key": int(row["customer_key"]),
                            "product_key": int(row["product_key"]),
                            "geo_key": int(row["geography_key"]),
                            "date_key": int(row["date_key"]),
                            "sales": float(row["sales"] or 0),
                            "late_delivery_risk": int(row["late_delivery_risk"] or 0)
                        })
                        insert_count += 1
                    except (SQLAlchemyError, IntegrityError, KeyError, ValueError) as e:
                        log(f"  ❌ Insert failed: {e}", "ERROR")
        
        log(f"✅ fact_orders: {insert_count:,} inserted/updated", "INFO")
        
        # Calculate metrics with division by zero protection
        otif_pct = (df_facts_valid["is_otif"].sum() / len(df_facts_valid) * 100) if len(df_facts_valid) > 0 else 0.0
        revenue_at_risk = df_facts_valid["revenue_at_risk"].sum()
        
        log(f"  📈 OTIF%: {otif_pct:.2f}%", "INFO")
        log(f"  💰 Revenue at Risk: ${revenue_at_risk:,.2f}", "INFO")
        
        return {
            "total_orders": len(df_facts),
            "inserted": insert_count,
            "skipped": skipped_count,
            "otif_pct": otif_pct,
            "revenue_at_risk": revenue_at_risk,
        }
        
    except (SQLAlchemyError, KeyError, ValueError, TypeError) as e:
        log(f"❌ Error in populate_fact_orders: {e}", "ERROR")
        raise


# ============================================================================
# MAIN ETL ORCHESTRATION
# ============================================================================


def run_etl_pipeline():
    """Orchestrate complete ETL pipeline: dimensions → facts."""
    start_time = datetime.now()
    etl_run_id = str(uuid.uuid4())
    
    log(
        f"\n{'=' * 80}\n"
        f"TORRE CONTROL - ETL PIPELINE: Stage → Star Schema\n"
        f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"ETL Run ID: {etl_run_id}\n"
        f"{'=' * 80}",
        "INFO"
    )
    
    engine = None
    
    try:
        engine = get_db_connection()
        
        # Verify schema exists before starting
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'dw' AND table_name = 'stg_raw_orders'"
            ))
            if result.scalar() == 0:
                log("\u274c Error: stg_raw_orders table not found. Run load_data.py first.", "ERROR")
                return 1
        
        customer_lookup = populate_dim_customer(engine)
        geography_lookup = populate_dim_geography(engine)
        product_lookup = populate_dim_product(engine)
        date_lookup = populate_dim_date(engine)
        fact_summary = populate_fact_orders(
            engine, customer_lookup, geography_lookup, product_lookup, date_lookup, etl_run_id
        )
        
        log("\n🔄 Marking staging as processed...", "INFO")
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE dw.stg_raw_orders SET is_processed = TRUE WHERE is_processed = FALSE")
            )
        log("✅ Staging marked as processed", "INFO")
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        log(
            f"\n{'=' * 80}\n"
            f"✅ ETL PIPELINE SUCCESSFUL\n"
            f"Elapsed Time: {elapsed:.1f} seconds\n"
            f"Fact Summary: {fact_summary}\n"
            f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'=' * 80}\n",
            "INFO"
        )
        
        return 0
        
    except SQLAlchemyError as e:
        log(f"\n❌ Database error: {e}", "ERROR")
        return 1
    except (KeyError, ValueError, TypeError) as e:
        log(f"\n❌ Data processing error: {e}", "ERROR")
        return 1
    except Exception as e:
        log(f"\n❌ Unexpected error: {type(e).__name__}: {e}", "ERROR")
        return 1
    finally:
        if engine:
            engine.dispose()
            log("✅ Database connection closed", "INFO")


if __name__ == "__main__":
    exit_code = run_etl_pipeline()
    exit(exit_code)
