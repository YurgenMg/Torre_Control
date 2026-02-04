#!/usr/bin/env python3
"""
Torre Control - Data Validation Module Tests
=============================================

Unit tests for the DataValidator class.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import pandas as pd
import pytest

from src.etl.validate import DataValidator, ValidationError


class TestDataValidator:
    """Test suite for DataValidator class."""
    
    def test_validator_initialization(self, validator):
        """Test that DataValidator initializes correctly."""
        assert validator is not None
        assert validator.settings is not None
        assert validator.loader is not None
        assert validator.logger is not None
        assert validator.validation_results == []
    
    def test_add_result(self, validator):
        """Test adding validation results."""
        validator._add_result("test_check", True, "Test passed", "INFO")
        
        assert len(validator.validation_results) == 1
        assert validator.validation_results[0]["check"] == "test_check"
        assert validator.validation_results[0]["passed"] == True
        assert validator.validation_results[0]["message"] == "Test passed"
        assert validator.validation_results[0]["severity"] == "INFO"
    
    @pytest.mark.database
    def test_validate_table_exists(self, validator, clean_database, loader):
        """Test table existence validation."""
        # Create a test table
        from sqlalchemy import text
        create_sql = """
            CREATE TABLE IF NOT EXISTS dw.test_table (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100)
            )
        """
        loader.execute_statement(create_sql)
        
        # Test that table exists
        exists = validator.validate_table_exists("test_table", schema="dw")
        assert exists == True
        
        # Test that non-existent table returns False
        exists = validator.validate_table_exists("nonexistent_table", schema="dw")
        assert exists == False
    
    @pytest.mark.database
    def test_validate_row_count(self, validator, clean_database, loader):
        """Test row count validation."""
        # Create and populate test table
        from sqlalchemy import text
        
        create_sql = """
            CREATE TABLE IF NOT EXISTS dw.test_table (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100)
            )
        """
        loader.execute_statement(create_sql)
        
        # Insert test data
        insert_sql = """
            INSERT INTO dw.test_table (id, name) VALUES 
            (1, 'test1'), (2, 'test2'), (3, 'test3')
        """
        loader.execute_statement(insert_sql)
        
        # Test row count validation
        passed, count = validator.validate_row_count("test_table", schema="dw", min_rows=1)
        assert passed == True
        assert count == 3
        
        # Test with higher minimum
        passed, count = validator.validate_row_count("test_table", schema="dw", min_rows=5)
        assert passed == False
        assert count == 3
    
    @pytest.mark.database
    def test_validate_no_nulls(self, validator, clean_database, loader):
        """Test NULL value validation."""
        from sqlalchemy import text
        
        # Create test table with some NULLs
        create_sql = """
            CREATE TABLE IF NOT EXISTS dw.test_table (
                id INTEGER,
                required_col VARCHAR(100),
                optional_col VARCHAR(100)
            )
        """
        loader.execute_statement(create_sql)
        
        # Insert data with NULLs
        insert_sql = """
            INSERT INTO dw.test_table (id, required_col, optional_col) VALUES 
            (1, 'value1', 'opt1'),
            (2, NULL, 'opt2'),
            (3, 'value3', NULL)
        """
        loader.execute_statement(insert_sql)
        
        # Validate no nulls in id column (should fail - id 2 has NULL in required_col)
        passed = validator.validate_no_nulls("test_table", ["required_col"], schema="dw")
        assert passed == False
        
        # Validate id column (no NULLs - should pass)
        passed = validator.validate_no_nulls("test_table", ["id"], schema="dw")
        assert passed == True


class TestValidationUtils:
    """Test validation utility functions."""
    
    def test_otif_validation_logic(self):
        """Test OTIF validation calculation."""
        from src.etl.utils import calculate_otif
        
        df = pd.DataFrame({
            "is_late": [False, True, False, True],
            "is_complete": [True, True, True, True],
            "is_canceled": [False, False, False, False]
        })
        
        otif = calculate_otif(df)
        
        # 2 out of 4 are on-time and complete = 50%
        assert otif == 50.0
    
    def test_revenue_at_risk_calculation(self):
        """Test revenue at risk calculation."""
        from src.etl.utils import calculate_revenue_at_risk
        
        df = pd.DataFrame({
            "is_late": [False, True, False, True, True],
            "sales": [100.0, 200.0, 150.0, 300.0, 250.0]
        })
        
        revenue_at_risk = calculate_revenue_at_risk(df)
        
        # Sum of sales where is_late = True: 200 + 300 + 250 = 750
        assert revenue_at_risk == 750.0
    
    def test_vip_customers_at_risk(self):
        """Test VIP customer at risk identification."""
        from src.etl.utils import identify_vip_customers_at_risk
        
        df = pd.DataFrame({
            "customer_id": ["C1", "C2", "C3", "C1", "C2", "C3", "C1", "C2"],
            "sales": [1000, 500, 100, 1000, 500, 100, 1000, 500],
            "is_late": [False, False, False, True, False, False, True, True]
        })
        
        vip_at_risk = identify_vip_customers_at_risk(df, top_percentile=0.4)
        
        # C1 and C2 should be VIP (top 40%)
        # Both have late orders
        assert len(vip_at_risk) > 0
        assert "C1" in vip_at_risk["customer_id"].values or "C2" in vip_at_risk["customer_id"].values


class TestValidationSummary:
    """Test validation summary generation."""
    
    def test_validation_summary_all_passed(self, validator):
        """Test summary when all checks pass."""
        validator._add_result("check1", True, "Pass 1", "INFO")
        validator._add_result("check2", True, "Pass 2", "INFO")
        validator._add_result("check3", True, "Pass 3", "INFO")
        
        # Mock validate_all to return summary
        total = len(validator.validation_results)
        passed = sum(1 for r in validator.validation_results if r["passed"])
        
        assert total == 3
        assert passed == 3
        assert passed / total == 1.0
    
    def test_validation_summary_with_failures(self, validator):
        """Test summary when some checks fail."""
        validator._add_result("check1", True, "Pass 1", "INFO")
        validator._add_result("check2", False, "Fail 2", "ERROR")
        validator._add_result("check3", True, "Pass 3", "INFO")
        validator._add_result("check4", False, "Fail 4", "WARNING")
        
        total = len(validator.validation_results)
        passed = sum(1 for r in validator.validation_results if r["passed"])
        failed = total - passed
        
        assert total == 4
        assert passed == 2
        assert failed == 2
        assert passed / total == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
