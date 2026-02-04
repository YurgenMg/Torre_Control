#!/usr/bin/env python3
"""
Transform Stage Layer to Star Schema (Dimensions + Facts)
Purpose: Convert stg_raw_orders into dim_customer, dim_geography, dim_product, 
         dim_date, and fact_orders with data quality validation.

Author: Data Engineering Team (Torre Control)
Date: 2026-02-04
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
        
        df_customers["customer_name"] = (
            df_customers["customer_fname"].fillna("") + " " + 
            df_customers["customer_lname"].fillna("")
        ).str.strip()
        
        df_customers["sales_per_customer"] = df_customers["sales_per_customer"].astype(float)
        
        critical_fields = ["customer_id", "customer_name"]
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
                    (customer_id, customer_name, customer_email, 
                     customer_segment, sales_per_customer, order_count)
                    VALUES (:customer_id, :customer_name, :customer_email, 
                            :customer_segment, :sales_per_customer, :order_count)
                    ON CONFLICT (customer_id) 
                    DO UPDATE SET 
                        customer_name = EXCLUDED.customer_name,
                        customer_email = EXCLUDED.customer_email,
                        customer_segment = EXCLUDED.customer_segment,
                        sales_per_customer = EXCLUDED.sales_per_customer,
                        order_count = EXCLUDED.order_count
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "customer_id": row["customer_id"],
                            "customer_name": row["customer_name"],
                            "customer_email": row["customer_email"],
                            "customer_segment": row["customer_segment"],
                            "sales_per_customer": row["sales_per_customer"],
                            "order_count": int(row["order_count"]),
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
    """Populate dim_geography from stg_raw_orders."""
    log("\n🔄 [2/5] Populating dim_geography...", "INFO")
    
    try:
        query = """
            SELECT DISTINCT
                stg.market,
                stg.order_region as region,
                stg.customer_country as country,
                stg.customer_state as state,
                stg.customer_city as city
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
        df_geo["state"] = df_geo["state"].fillna("Unknown")
        df_geo["city"] = df_geo["city"].fillna("Unknown")
        
        log(f"  ✅ Validated {len(df_geo):,} geographic records", "INFO")
        
        insert_count = 0
        
        with engine.begin() as conn:
            for _, row in tqdm(df_geo.iterrows(), total=len(df_geo), desc="  Inserting geographies"):
                upsert_query = text("""
                    INSERT INTO dw.dim_geography 
                    (market, region, country, state, city)
                    VALUES (:market, :region, :country, :state, :city)
                    ON CONFLICT (market, region, country, state, city)
                    DO NOTHING
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "market": row["market"],
                            "region": row["region"],
                            "country": row["country"],
                            "state": row["state"],
                            "city": row["city"],
                        }
                    )
                    insert_count += 1
                except Exception as e:
                    log(f"  ⚠️  Error inserting geography: {e}", "WARNING")
        
        log(f"✅ dim_geography: {insert_count:,} inserted", "INFO")
        
        with engine.connect() as conn:
            df_geo_lookup = pd.read_sql_query(
                "SELECT market, region, country, state, city, geography_id FROM dw.dim_geography", conn
            )
        
        lookup_dict = {}
        for _, row in df_geo_lookup.iterrows():
            key = (row["market"], row["region"], row["country"], row["state"], row["city"])
            lookup_dict[key] = row["geography_id"]
        
        log(f"  📌 Geography lookup dict: {len(lookup_dict)} entries", "INFO")
        
        return lookup_dict
        
    except Exception as e:
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
                    (product_id, product_name, category_name, department_name, product_price)
                    VALUES (:product_id, :product_name, :category_name, :department_name, :product_price)
                    ON CONFLICT (product_id) 
                    DO NOTHING
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "product_id": row["product_card_id"],
                            "product_name": row["product_name"],
                            "category_name": row["category_name"],
                            "department_name": row["department_name"],
                            "product_price": float(row["product_price"]),
                        }
                    )
                    insert_count += 1
                except Exception as e:
                    log(f"  ⚠️  Error inserting product {row['product_card_id']}: {e}", "WARNING")
        
        log(f"✅ dim_product: {insert_count:,} inserted", "INFO")
        
        with engine.connect() as conn:
            df_lookup = pd.read_sql_query("SELECT product_id, product_key FROM dw.dim_product", conn)
        
        lookup_dict = dict(zip(df_lookup["product_id"], df_lookup["product_key"]))
        log(f"  📌 Product lookup dict: {len(lookup_dict)} entries", "INFO")
        
        return lookup_dict
        
    except Exception as e:
        log(f"❌ Error in populate_dim_product: {e}", "ERROR")
        raise


def populate_dim_date(engine):
    """Populate dim_date from stg_raw_orders."""
    log("\n🔄 [4/5] Populating dim_date...", "INFO")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        MIN(stg.order_date) as min_date,
                        MAX(stg.order_date) as max_date
                    FROM dw.stg_raw_orders stg
                    WHERE stg.order_date IS NOT NULL
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
        
        with engine.begin() as conn:
            for _, row in tqdm(df_dates.iterrows(), total=len(df_dates), desc="  Inserting dates"):
                upsert_query = text("""
                    INSERT INTO dw.dim_date 
                    (date_id, order_date, year, quarter, month, week, 
                     day_of_month, day_of_week, month_name, day_name, is_weekend)
                    VALUES (:date_id, :order_date, :year, :quarter, :month, :week, 
                            :day_of_month, :day_of_week, :month_name, :day_name, :is_weekend)
                    ON CONFLICT (date_id)
                    DO NOTHING
                """)
                
                try:
                    conn.execute(
                        upsert_query,
                        {
                            "date_id": int(row["date_id"]),
                            "order_date": row["order_date"],
                            "year": int(row["year"]),
                            "quarter": int(row["quarter"]),
                            "month": int(row["month"]),
                            "week": int(row["week"]),
                            "day_of_month": int(row["day_of_month"]),
                            "day_of_week": int(row["day_of_week"]),
                            "month_name": row["month_name"],
                            "day_name": row["day_name"],
                            "is_weekend": int(row["is_weekend"]),
                        }
                    )
                    insert_count += 1
                except Exception as e:
                    log(f"  ⚠️  Error inserting date {row['date_id']}: {e}", "WARNING")
        
        log(f"✅ dim_date: {insert_count:,} inserted", "INFO")
        
        lookup_dict = dict(zip(df_dates["order_date"], df_dates["date_id"]))
        log(f"  📌 Date lookup dict: {len(lookup_dict)} entries", "INFO")
        
        return lookup_dict
        
    except Exception as e:
        log(f"❌ Error in populate_dim_date: {e}", "ERROR")
        raise


def populate_fact_orders(engine, customer_lookup, geography_lookup, product_lookup, date_lookup, etl_run_id):
    """Populate fact_orders from stg_raw_orders."""
    log("\n🔄 [5/5] Populating fact_orders...", "INFO")
    
    try:
        query = """
            SELECT 
                stg.order_id, stg.order_item_id, stg.customer_id, stg.market,
                stg.order_region, stg.customer_country, stg.customer_state, stg.customer_city,
                stg.product_card_id, stg.order_date, stg.sales, stg.benefit_per_order,
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
        
        df_facts["customer_key"] = df_facts["customer_id"].map(customer_lookup)
        df_facts["geography_key"] = df_facts.apply(
            lambda row: geography_lookup.get(
                (row["market"], row["order_region"], row["customer_country"], 
                 row["customer_state"], row["customer_city"])
            ), axis=1
        )
        df_facts["product_key"] = df_facts["product_card_id"].map(product_lookup)
        df_facts["date_key"] = pd.to_datetime(df_facts["order_date"]).map(date_lookup)
        
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
                        (order_id, order_item_id, customer_key, geography_key, product_key, 
                         date_key, sales, benefit_per_order, quantity, order_item_total, 
                         profit_ratio, late_delivery_risk, days_real, days_scheduled, 
                         delivery_status, discount_rate, is_otif, revenue_at_risk, etl_run_id)
                        VALUES (:order_id, :order_item_id, :customer_key, :geography_key, :product_key, 
                                :date_key, :sales, :benefit_per_order, :quantity, :order_item_total, 
                                :profit_ratio, :late_delivery_risk, :days_real, :days_scheduled, 
                                :delivery_status, :discount_rate, :is_otif, :revenue_at_risk, :etl_run_id)
                        ON CONFLICT (order_id, order_item_id)
                        DO UPDATE SET
                            sales = EXCLUDED.sales,
                            benefit_per_order = EXCLUDED.benefit_per_order,
                            quantity = EXCLUDED.quantity,
                            order_item_total = EXCLUDED.order_item_total,
                            profit_ratio = EXCLUDED.profit_ratio,
                            late_delivery_risk = EXCLUDED.late_delivery_risk,
                            days_real = EXCLUDED.days_real,
                            days_scheduled = EXCLUDED.days_scheduled,
                            delivery_status = EXCLUDED.delivery_status,
                            discount_rate = EXCLUDED.discount_rate,
                            is_otif = EXCLUDED.is_otif,
                            revenue_at_risk = EXCLUDED.revenue_at_risk
                    """)
                    
                    try:
                        conn.execute(upsert_query, {
                            "order_id": str(row["order_id"]),
                            "order_item_id": str(row["order_item_id"]),
                            "customer_key": int(row["customer_key"]),
                            "geography_key": int(row["geography_key"]),
                            "product_key": int(row["product_key"]),
                            "date_key": int(row["date_key"]),
                            "sales": float(row["sales"] or 0),
                            "benefit_per_order": float(row["benefit_per_order"] or 0),
                            "quantity": int(row["order_item_quantity"] or 0),
                            "order_item_total": float(row["order_item_total"] or 0),
                            "profit_ratio": float(row["order_item_profit_ratio"] or 0),
                            "late_delivery_risk": int(row["late_delivery_risk"] or 0),
                            "days_real": int(row["days_for_shipping_real"] or 0),
                            "days_scheduled": int(row["days_for_shipment_scheduled"] or 0),
                            "delivery_status": str(row["delivery_status"] or "UNKNOWN"),
                            "discount_rate": float(row["order_item_discount_rate"] or 0),
                            "is_otif": int(row["is_otif"]),
                            "revenue_at_risk": float(row["revenue_at_risk"]),
                            "etl_run_id": row["etl_run_id"],
                        })
                        insert_count += 1
                    except Exception as e:
                        log(f"  ❌ Insert failed: {e}", "ERROR")
        
        log(f"✅ fact_orders: {insert_count:,} inserted/updated", "INFO")
        
        otif_pct = (df_facts_valid["is_otif"].sum() / len(df_facts_valid)) * 100
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
        
    except Exception as e:
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
    except Exception as e:
        log(f"\n❌ Unexpected error: {e}", "ERROR")
        return 1
    finally:
        if engine:
            engine.dispose()
            log("✅ Database connection closed", "INFO")


if __name__ == "__main__":
    exit_code = run_etl_pipeline()
    exit(exit_code)
