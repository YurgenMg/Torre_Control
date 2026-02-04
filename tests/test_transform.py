#!/usr/bin/env python3
"""
Torre Control - Data Transformation Module Tests
=================================================

Unit tests for the DataTransformer class.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import pytest

from src.etl.transform import DataTransformer


class TestDataTransformer:
    """Test suite for DataTransformer class."""
    
    def test_transformer_initialization(self, transformer):
        """Test that DataTransformer initializes correctly."""
        assert transformer is not None
        assert transformer.settings is not None
        assert transformer.loader is not None
        assert transformer.logger is not None
    
    @pytest.mark.database
    @pytest.mark.slow
    def test_create_dim_customer(self, transformer, clean_database, loader, sample_dataframe):
        """Test customer dimension creation."""
        # First, load sample data into staging table
        df_sanitized = sample_dataframe.copy()
        df_sanitized.columns = [col.lower().replace(" ", "_") for col in df_sanitized.columns]
        
        # Add required columns
        if "customer_city" not in df_sanitized.columns:
            df_sanitized["customer_city"] = "Test City"
        if "customer_state" not in df_sanitized.columns:
            df_sanitized["customer_state"] = "Test State"
        if "customer_country" not in df_sanitized.columns:
            df_sanitized["customer_country"] = "Test Country"
        
        # Load into staging table
        loader.load_dataframe(
            df=df_sanitized,
            table_name="stg_raw_orders",
            schema="dw",
            if_exists="replace"
        )
        
        # Create customer dimension table structure
        from sqlalchemy import text
        create_dim_sql = """
            CREATE TABLE IF NOT EXISTS dw.dim_customer (
                customer_id VARCHAR(50) PRIMARY KEY,
                customer_fname VARCHAR(100),
                customer_lname VARCHAR(100),
                customer_email VARCHAR(200),
                customer_segment VARCHAR(50),
                customer_city VARCHAR(100),
                customer_state VARCHAR(100),
                customer_country VARCHAR(100),
                sales_per_customer NUMERIC(15, 2)
            )
        """
        loader.execute_statement(create_dim_sql)
        
        # Test dimension creation
        rows = transformer.create_dim_customer()
        
        assert rows > 0
        
        # Verify data in dimension table
        count = loader.get_table_count("dim_customer", schema="dw")
        assert count > 0
    
    @pytest.mark.database
    @pytest.mark.slow
    def test_create_dim_product(self, transformer, clean_database, loader, sample_dataframe):
        """Test product dimension creation."""
        # Prepare staging data
        df_sanitized = sample_dataframe.copy()
        df_sanitized.columns = [col.lower().replace(" ", "_") for col in df_sanitized.columns]
        
        # Add order_item_product_price if not exists
        if "order_item_product_price" not in df_sanitized.columns:
            df_sanitized["order_item_product_price"] = df_sanitized.get("sales", 100.0)
        
        # Rename category_id if needed
        if "category_id" not in df_sanitized.columns and "category_name" in df_sanitized.columns:
            df_sanitized["category_id"] = df_sanitized["category_name"].astype("category").cat.codes
        
        loader.load_dataframe(
            df=df_sanitized,
            table_name="stg_raw_orders",
            schema="dw",
            if_exists="replace"
        )
        
        # Create product dimension table structure
        from sqlalchemy import text
        create_dim_sql = """
            CREATE TABLE IF NOT EXISTS dw.dim_product (
                product_card_id INTEGER PRIMARY KEY,
                category_id INTEGER,
                category_name VARCHAR(100),
                department_name VARCHAR(100),
                product_name VARCHAR(200),
                product_price NUMERIC(15, 2)
            )
        """
        loader.execute_statement(create_dim_sql)
        
        # Test dimension creation
        rows = transformer.create_dim_product()
        
        assert rows > 0
    
    def test_transformer_with_mock_loader(self, mocker):
        """Test transformer with mocked loader."""
        # Create mock loader
        mock_loader = mocker.MagicMock()
        
        # Create transformer with mock
        transformer = DataTransformer(loader=mock_loader)
        
        assert transformer.loader == mock_loader


class TestTransformationLogic:
    """Test transformation logic and calculations."""
    
    def test_otif_calculation_logic(self):
        """Test OTIF (On-Time In-Full) calculation logic."""
        import pandas as pd
        
        df = pd.DataFrame({
            "days_for_shipping_real": [5, 7, 3, 10],
            "days_for_shipment_scheduled": [5, 5, 5, 5],
            "delivery_status": ["Complete", "Complete", "Complete", "Complete"],
            "order_status": ["COMPLETE", "COMPLETE", "COMPLETE", "COMPLETE"]
        })
        
        # Calculate is_late
        df["is_late"] = df["days_for_shipping_real"] > df["days_for_shipment_scheduled"]
        
        # Calculate is_complete
        df["is_complete"] = df["delivery_status"].str.upper().str.contains("COMPLETE")
        
        # Calculate OTIF
        otif_orders = df[(df["is_late"] == False) & (df["is_complete"] == True)]
        otif_pct = 100.0 * len(otif_orders) / len(df)
        
        # Should be 50% (2 out of 4 orders are on-time and complete)
        assert otif_pct == 50.0
    
    def test_delay_calculation(self):
        """Test delay days calculation."""
        import pandas as pd
        
        df = pd.DataFrame({
            "days_for_shipping_real": [5, 7, 3, 10],
            "days_for_shipment_scheduled": [5, 5, 5, 5]
        })
        
        # Calculate delay
        df["delay_days"] = df["days_for_shipping_real"] - df["days_for_shipment_scheduled"]
        df["delay_days"] = df["delay_days"].clip(lower=0)  # No negative delays
        
        expected_delays = [0, 2, 0, 5]
        assert list(df["delay_days"]) == expected_delays


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
