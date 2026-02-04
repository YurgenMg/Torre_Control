#!/usr/bin/env python3
"""
Torre Control - Data Extraction Module Tests
=============================================

Unit tests for the DataExtractor class.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import pandas as pd
import pytest

from src.etl.extract import DataExtractor


class TestDataExtractor:
    """Test suite for DataExtractor class."""
    
    def test_extractor_initialization(self, extractor):
        """Test that DataExtractor initializes correctly."""
        assert extractor is not None
        assert extractor.settings is not None
        assert extractor.logger is not None
    
    def test_extract_csv_from_file(self, extractor, sample_csv_file):
        """Test CSV extraction from a file."""
        df = extractor.extract_csv(file_path=str(sample_csv_file))
        
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0
    
    def test_extract_csv_missing_file(self, extractor):
        """Test that extracting non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            extractor.extract_csv(file_path="/nonexistent/path/file.csv")
    
    def test_sanitize_column_names(self, extractor, sample_dataframe):
        """Test column name sanitization."""
        # Create DataFrame with problematic column names
        df = sample_dataframe.copy()
        
        # Sanitize columns
        df_sanitized = extractor.sanitize_column_names(df)
        
        # Check that columns are sanitized
        for col in df_sanitized.columns:
            # Should be lowercase
            assert col == col.lower(), f"Column {col} is not lowercase"
            
            # Should not contain spaces
            assert " " not in col, f"Column {col} contains spaces"
            
            # Should not contain parentheses
            assert "(" not in col and ")" not in col, f"Column {col} contains parentheses"
    
    def test_sanitize_column_names_specific_cases(self, extractor):
        """Test specific column name sanitization cases."""
        df = pd.DataFrame({
            "Order Id": [1],
            "Customer ID": [1],
            "Order Date (DateOrders)": ["2023-01-01"],
            "Sales per customer": [100.0],
            "Days for shipping (real)": [5]
        })
        
        df_sanitized = extractor.sanitize_column_names(df)
        
        expected_columns = [
            "order_id",
            "customer_id",
            "order_date_dateorders",
            "sales_per_customer",
            "days_for_shipping_real"
        ]
        
        assert list(df_sanitized.columns) == expected_columns
    
    def test_extract_and_sanitize(self, extractor, sample_csv_file):
        """Test combined extract and sanitize operation."""
        df = extractor.extract_and_sanitize(file_path=str(sample_csv_file))
        
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # Check that columns are sanitized
        for col in df.columns:
            assert col == col.lower()
            assert " " not in col
    
    def test_get_data_profile(self, extractor, sample_dataframe):
        """Test data profiling functionality."""
        profile = extractor.get_data_profile(sample_dataframe)
        
        assert profile is not None
        assert "row_count" in profile
        assert "column_count" in profile
        assert "columns" in profile
        assert "dtypes" in profile
        assert "null_counts" in profile
        assert "null_percentages" in profile
        assert "memory_mb" in profile
        
        # Check values
        assert profile["row_count"] == len(sample_dataframe)
        assert profile["column_count"] == len(sample_dataframe.columns)
    
    def test_get_data_profile_with_nulls(self, extractor):
        """Test data profiling with null values."""
        df = pd.DataFrame({
            "col1": [1, 2, None, 4, 5],
            "col2": [None, None, None, None, None],
            "col3": [1, 2, 3, 4, 5]
        })
        
        profile = extractor.get_data_profile(df)
        
        # Check null counts
        assert profile["null_counts"]["col1"] == 1
        assert profile["null_counts"]["col2"] == 5
        assert profile["null_counts"]["col3"] == 0
        
        # Check null percentages
        assert profile["null_percentages"]["col1"] == 20.0
        assert profile["null_percentages"]["col2"] == 100.0
        assert profile["null_percentages"]["col3"] == 0.0
    
    @pytest.mark.slow
    def test_extract_csv_with_chunking(self, extractor, sample_csv_file):
        """Test CSV extraction with chunking."""
        df = extractor.extract_csv(
            file_path=str(sample_csv_file),
            chunksize=2
        )
        
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
