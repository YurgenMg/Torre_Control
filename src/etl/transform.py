#!/usr/bin/env python3
"""
Torre Control - Data Transformation Module
===========================================

Handles transformation of staging data into star schema (dimensions + facts).

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

from typing import Optional

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from src.config import get_settings
from src.etl.load import DataLoader
from src.logging_config import LoggerMixin, log_execution_time


class DataTransformer(LoggerMixin):
    """
    Transforms staging data into star schema.
    
    Creates dimension and fact tables with calculated columns and quality flags.
    """
    
    def __init__(self, loader: Optional[DataLoader] = None):
        """
        Initialize DataTransformer.
        
        Args:
            loader: DataLoader instance (creates new if not provided)
        """
        self.settings = get_settings()
        self.loader = loader or DataLoader()
        self.logger.info("DataTransformer initialized")
    
    @log_execution_time
    def create_dim_customer(self) -> int:
        """
        Create customer dimension from staging table.
        
        Returns:
            int: Number of rows created
        """
        self.logger.info("Creating dim_customer...")
        
        query = """
            INSERT INTO dw.dim_customer (
                customer_id,
                customer_fname,
                customer_lname,
                customer_email,
                customer_segment,
                customer_city,
                customer_state,
                customer_country,
                sales_per_customer
            )
            SELECT 
                customer_id,
                customer_fname,
                customer_lname,
                customer_email,
                customer_segment,
                customer_city,
                customer_state,
                customer_country,
                SUM(COALESCE(sales, 0)) as sales_per_customer
            FROM dw.stg_raw_orders
            WHERE customer_id IS NOT NULL
            GROUP BY 
                customer_id,
                customer_fname,
                customer_lname,
                customer_email,
                customer_segment,
                customer_city,
                customer_state,
                customer_country
            ON CONFLICT (customer_id) DO UPDATE SET
                sales_per_customer = EXCLUDED.sales_per_customer
        """
        
        try:
            rows = self.loader.execute_statement(query)
            self.logger.info(f"✅ dim_customer created: {rows:,} rows")
            return rows
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create dim_customer: {e}")
            raise
    
    @log_execution_time
    def create_dim_product(self) -> int:
        """
        Create product dimension from staging table.
        
        Returns:
            int: Number of rows created
        """
        self.logger.info("Creating dim_product...")
        
        query = """
            INSERT INTO dw.dim_product (
                product_card_id,
                category_id,
                category_name,
                department_name,
                product_name,
                product_price
            )
            SELECT DISTINCT
                product_card_id,
                category_id,
                category_name,
                department_name,
                product_name,
                order_item_product_price as product_price
            FROM dw.stg_raw_orders
            WHERE product_card_id IS NOT NULL
            ON CONFLICT (product_card_id) DO UPDATE SET
                product_name = EXCLUDED.product_name,
                product_price = EXCLUDED.product_price
        """
        
        try:
            rows = self.loader.execute_statement(query)
            self.logger.info(f"✅ dim_product created: {rows:,} rows")
            return rows
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create dim_product: {e}")
            raise
    
    @log_execution_time
    def create_dim_geography(self) -> int:
        """
        Create geography dimension from staging table.
        
        Returns:
            int: Number of rows created
        """
        self.logger.info("Creating dim_geography...")
        
        query = """
            INSERT INTO dw.dim_geography (
                geography_key,
                market,
                order_region,
                order_country,
                order_state,
                order_city
            )
            SELECT DISTINCT
                MD5(CONCAT(
                    COALESCE(market, ''), '|',
                    COALESCE(order_region, ''), '|',
                    COALESCE(order_country, ''), '|',
                    COALESCE(order_state, ''), '|',
                    COALESCE(order_city, '')
                )) as geography_key,
                market,
                order_region,
                order_country,
                order_state,
                order_city
            FROM dw.stg_raw_orders
            WHERE market IS NOT NULL
            ON CONFLICT (geography_key) DO NOTHING
        """
        
        try:
            rows = self.loader.execute_statement(query)
            self.logger.info(f"✅ dim_geography created: {rows:,} rows")
            return rows
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create dim_geography: {e}")
            raise
    
    @log_execution_time
    def create_dim_date(self) -> int:
        """
        Create date dimension from staging table.
        
        Returns:
            int: Number of rows created
        """
        self.logger.info("Creating dim_date...")
        
        query = """
            INSERT INTO dw.dim_date (
                date_key,
                full_date,
                year,
                quarter,
                month,
                month_name,
                week,
                day_of_year,
                day_of_month,
                day_of_week,
                day_name
            )
            SELECT DISTINCT
                TO_CHAR(order_date_dateorders, 'YYYYMMDD')::INTEGER as date_key,
                order_date_dateorders::DATE as full_date,
                EXTRACT(YEAR FROM order_date_dateorders) as year,
                EXTRACT(QUARTER FROM order_date_dateorders) as quarter,
                EXTRACT(MONTH FROM order_date_dateorders) as month,
                TO_CHAR(order_date_dateorders, 'Month') as month_name,
                EXTRACT(WEEK FROM order_date_dateorders) as week,
                EXTRACT(DOY FROM order_date_dateorders) as day_of_year,
                EXTRACT(DAY FROM order_date_dateorders) as day_of_month,
                EXTRACT(DOW FROM order_date_dateorders) as day_of_week,
                TO_CHAR(order_date_dateorders, 'Day') as day_name
            FROM dw.stg_raw_orders
            WHERE order_date_dateorders IS NOT NULL
            ON CONFLICT (date_key) DO NOTHING
        """
        
        try:
            rows = self.loader.execute_statement(query)
            self.logger.info(f"✅ dim_date created: {rows:,} rows")
            return rows
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create dim_date: {e}")
            raise
    
    @log_execution_time
    def create_fact_orders(self) -> int:
        """
        Create fact orders table with calculated columns.
        
        Returns:
            int: Number of rows created
        """
        self.logger.info("Creating fact_orders...")
        
        query = """
            INSERT INTO dw.fact_orders (
                order_id,
                order_item_id,
                customer_id,
                product_card_id,
                date_key,
                geography_key,
                sales,
                order_item_quantity,
                order_item_total,
                order_item_discount,
                order_item_discount_rate,
                order_item_profit_ratio,
                benefit_per_order,
                days_for_shipment_scheduled,
                days_for_shipping_real,
                delivery_status,
                late_delivery_risk,
                order_status,
                shipping_mode,
                -- Calculated columns
                is_late,
                delay_days,
                is_complete,
                is_canceled,
                is_fraud_suspect
            )
            SELECT 
                order_id,
                order_item_id,
                customer_id,
                product_card_id,
                TO_CHAR(order_date_dateorders, 'YYYYMMDD')::INTEGER as date_key,
                MD5(CONCAT(
                    COALESCE(market, ''), '|',
                    COALESCE(order_region, ''), '|',
                    COALESCE(order_country, ''), '|',
                    COALESCE(order_state, ''), '|',
                    COALESCE(order_city, '')
                )) as geography_key,
                sales,
                order_item_quantity,
                order_item_total,
                order_item_discount,
                order_item_discount_rate,
                order_item_profit_ratio,
                benefit_per_order,
                days_for_shipment_scheduled,
                days_for_shipping_real,
                delivery_status,
                late_delivery_risk,
                order_status,
                shipping_mode,
                -- Calculated columns
                CASE 
                    WHEN days_for_shipping_real > days_for_shipment_scheduled THEN TRUE 
                    ELSE FALSE 
                END as is_late,
                GREATEST(0, days_for_shipping_real - days_for_shipment_scheduled) as delay_days,
                CASE 
                    WHEN UPPER(delivery_status) LIKE '%COMPLETE%' THEN TRUE 
                    ELSE FALSE 
                END as is_complete,
                CASE 
                    WHEN UPPER(order_status) LIKE '%CANCEL%' THEN TRUE 
                    ELSE FALSE 
                END as is_canceled,
                CASE 
                    WHEN UPPER(order_status) LIKE '%FRAUD%' 
                         OR UPPER(delivery_status) LIKE '%SUSPECT%'
                         OR order_item_discount_rate > 50 
                    THEN TRUE 
                    ELSE FALSE 
                END as is_fraud_suspect
            FROM dw.stg_raw_orders
            WHERE order_id IS NOT NULL 
              AND order_item_id IS NOT NULL
            ON CONFLICT (order_id, order_item_id) DO UPDATE SET
                sales = EXCLUDED.sales,
                late_delivery_risk = EXCLUDED.late_delivery_risk
        """
        
        try:
            rows = self.loader.execute_statement(query)
            self.logger.info(f"✅ fact_orders created: {rows:,} rows")
            return rows
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create fact_orders: {e}")
            raise
    
    @log_execution_time
    def transform_all(self) -> dict:
        """
        Execute all transformation steps in sequence.
        
        Returns:
            dict: Row counts for each table created
        """
        self.logger.info("Starting full transformation pipeline...")
        
        results = {}
        
        try:
            # Create dimensions first
            results["dim_customer"] = self.create_dim_customer()
            results["dim_product"] = self.create_dim_product()
            results["dim_geography"] = self.create_dim_geography()
            results["dim_date"] = self.create_dim_date()
            
            # Create fact table
            results["fact_orders"] = self.create_fact_orders()
            
            self.logger.info("✅ All transformations completed successfully")
            self.logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Transformation pipeline failed: {e}")
            raise


if __name__ == "__main__":
    # Test transformer
    transformer = DataTransformer()
    
    try:
        results = transformer.transform_all()
        print("\nTransformation Results:")
        for table, count in results.items():
            print(f"  {table}: {count:,} rows")
    except Exception as e:
        print(f"Transformation failed: {e}")
