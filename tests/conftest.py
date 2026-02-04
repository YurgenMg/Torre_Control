#!/usr/bin/env python3
"""
Torre Control - Pytest Configuration and Fixtures
==================================================

Shared test fixtures and configuration for the Torre Control test suite.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import os
import sys
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Settings, get_settings
from src.etl.extract import DataExtractor
from src.etl.load import DataLoader
from src.etl.transform import DataTransformer
from src.etl.validate import DataValidator


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_settings():
    """
    Provide test settings.
    
    Override settings for test environment.
    """
    # Set environment to test
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    settings = Settings()
    return settings


@pytest.fixture(scope="session")
def test_database_url(test_settings):
    """Provide test database URL."""
    return test_settings.database_url


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_dataframe():
    """
    Provide a sample DataFrame for testing.
    
    Simulates DataCo supply chain dataset structure.
    """
    data = {
        "Order Id": [1, 2, 3, 4, 5],
        "Order Item Id": [1, 2, 3, 4, 5],
        "Customer ID": ["CUST001", "CUST002", "CUST003", "CUST001", "CUST002"],
        "Customer Fname": ["John", "Jane", "Bob", "John", "Jane"],
        "Customer Lname": ["Doe", "Smith", "Johnson", "Doe", "Smith"],
        "Customer Email": ["john@example.com", "jane@example.com", "bob@example.com", "john@example.com", "jane@example.com"],
        "Customer Segment": ["Consumer", "Corporate", "Home Office", "Consumer", "Corporate"],
        "Product Card Id": [101, 102, 103, 101, 104],
        "Category Name": ["Furniture", "Technology", "Office Supplies", "Furniture", "Technology"],
        "Department Name": ["Furniture", "Technology", "Office", "Furniture", "Technology"],
        "Product Name": ["Chair", "Laptop", "Pen", "Chair", "Phone"],
        "Sales": [100.0, 500.0, 10.0, 150.0, 300.0],
        "Order Item Quantity": [1, 1, 10, 2, 1],
        "Days for shipment (scheduled)": [5, 3, 2, 5, 3],
        "Days for shipping (real)": [7, 3, 2, 5, 4],
        "Delivery Status": ["Late shipment", "Shipping on time", "Advance shipping", "Shipping on time", "Late shipment"],
        "Late_delivery_risk": [1, 0, 0, 0, 1],
        "Order Status": ["COMPLETE", "COMPLETE", "COMPLETE", "COMPLETE", "COMPLETE"],
        "Market": ["USCA", "Europe", "LATAM", "USCA", "Europe"],
        "Order Region": ["East", "West", "South", "East", "West"],
        "Order Country": ["USA", "UK", "Brazil", "USA", "UK"],
        "Order State": ["NY", "London", "SP", "NY", "London"],
        "Order City": ["New York", "London", "Sao Paulo", "New York", "London"],
    }
    
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def sample_csv_file(tmp_path, sample_dataframe):
    """
    Create a temporary CSV file for testing.
    
    Args:
        tmp_path: Pytest temporary directory fixture
        sample_dataframe: Sample data fixture
    
    Returns:
        Path: Path to temporary CSV file
    """
    csv_path = tmp_path / "test_data.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    return csv_path


# ============================================================================
# ETL Component Fixtures
# ============================================================================

@pytest.fixture
def extractor():
    """Provide DataExtractor instance."""
    return DataExtractor()


@pytest.fixture
def loader(test_database_url):
    """Provide DataLoader instance."""
    return DataLoader(database_url=test_database_url)


@pytest.fixture
def transformer(loader):
    """Provide DataTransformer instance."""
    return DataTransformer(loader=loader)


@pytest.fixture
def validator(loader):
    """Provide DataValidator instance."""
    return DataValidator(loader=loader)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """
    Create test database engine.
    
    Scope: session - shared across all tests.
    """
    engine = create_engine(test_database_url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture
def clean_database(test_engine):
    """
    Clean test database before each test.
    
    Drops and recreates test schema.
    """
    from sqlalchemy import text
    
    with test_engine.connect() as conn:
        # Drop schema if exists
        conn.execute(text("DROP SCHEMA IF EXISTS dw CASCADE"))
        conn.commit()
        
        # Create schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dw"))
        conn.commit()
    
    yield
    
    # Cleanup after test (optional)
    # Uncomment if you want to clean after each test
    # with test_engine.connect() as conn:
    #     conn.execute(text("DROP SCHEMA IF EXISTS dw CASCADE"))
    #     conn.commit()


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_logger(monkeypatch):
    """
    Mock logger for testing without actual logging.
    
    Useful for tests that don't need real log output.
    """
    import logging
    
    # Create a mock logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # Remove all handlers
    
    return logger


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Provide temporary output directory for tests.
    
    Args:
        tmp_path: Pytest temporary directory fixture
    
    Returns:
        Path: Path to temporary output directory
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """
    Pytest configuration hook.
    
    Register custom markers and configure test environment.
    """
    # Register custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database connection"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection.
    
    Add markers to tests based on their location/name.
    """
    for item in items:
        # Add 'database' marker to tests that use database fixtures
        if "loader" in item.fixturenames or "test_engine" in item.fixturenames:
            item.add_marker(pytest.mark.database)
        
        # Add 'integration' marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add 'unit' marker to unit tests
        elif "unit" in item.nodeid or "test_" in item.name:
            item.add_marker(pytest.mark.unit)
