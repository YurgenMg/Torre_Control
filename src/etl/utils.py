#!/usr/bin/env python3
"""
Torre Control - ETL Utilities
==============================

Helper functions and utilities for ETL pipeline.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def sanitize_column_name(column_name: str) -> str:
    """
    Sanitize column name for database compatibility.
    
    Args:
        column_name: Original column name
    
    Returns:
        str: Sanitized column name
    """
    # Convert to lowercase and replace spaces with underscores
    sanitized = column_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    # Remove special characters except underscores
    sanitized = "".join(c if c.isalnum() or c == "_" else "" for c in sanitized)
    # Remove leading/trailing underscores and collapse multiple underscores
    sanitized = "_".join(filter(None, sanitized.split("_")))
    return sanitized


def sanitize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize all column names in a DataFrame.
    
    Args:
        df: DataFrame with raw column names
    
    Returns:
        pd.DataFrame: DataFrame with sanitized column names
    """
    df.columns = [sanitize_column_name(col) for col in df.columns]
    return df


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in MB.
    
    Args:
        file_path: Path to file
    
    Returns:
        float: File size in MB
    """
    return os.path.getsize(file_path) / (1024 * 1024)


def get_dataframe_memory_mb(df: pd.DataFrame) -> float:
    """
    Get DataFrame memory usage in MB.
    
    Args:
        df: DataFrame
    
    Returns:
        float: Memory usage in MB
    """
    return df.memory_usage(deep=True).sum() / (1024 * 1024)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        str: Formatted duration (e.g., "2h 34m 12s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def calculate_otif(
    df: pd.DataFrame,
    late_column: str = "is_late",
    complete_column: str = "is_complete",
    canceled_column: str = "is_canceled"
) -> float:
    """
    Calculate OTIF (On-Time In-Full) percentage.
    
    Args:
        df: DataFrame with order data
        late_column: Column indicating late delivery
        complete_column: Column indicating complete delivery
        canceled_column: Column indicating canceled orders
    
    Returns:
        float: OTIF percentage
    """
    # Filter out canceled orders
    active_orders = df[df[canceled_column] == False]
    
    if len(active_orders) == 0:
        return 0.0
    
    # OTIF = On-Time AND Complete
    otif_orders = active_orders[
        (active_orders[late_column] == False) & 
        (active_orders[complete_column] == True)
    ]
    
    otif_pct = 100.0 * len(otif_orders) / len(active_orders)
    
    return round(otif_pct, 2)


def calculate_revenue_at_risk(
    df: pd.DataFrame,
    late_column: str = "is_late",
    sales_column: str = "sales"
) -> float:
    """
    Calculate total revenue at risk from late deliveries.
    
    Args:
        df: DataFrame with order data
        late_column: Column indicating late delivery
        sales_column: Column with sales amount
    
    Returns:
        float: Total revenue at risk
    """
    late_orders = df[df[late_column] == True]
    revenue_at_risk = late_orders[sales_column].sum()
    
    return round(revenue_at_risk, 2)


def identify_vip_customers_at_risk(
    df: pd.DataFrame,
    customer_column: str = "customer_id",
    sales_column: str = "sales",
    late_column: str = "is_late",
    top_percentile: float = 0.1
) -> pd.DataFrame:
    """
    Identify VIP customers (top X%) with recent late deliveries.
    
    Args:
        df: DataFrame with order data
        customer_column: Customer ID column
        sales_column: Sales amount column
        late_column: Late delivery indicator column
        top_percentile: Top percentile to consider VIP (default: 0.1 = top 10%)
    
    Returns:
        pd.DataFrame: VIP customers at risk
    """
    # Calculate total sales per customer
    customer_sales = df.groupby(customer_column)[sales_column].sum().reset_index()
    customer_sales.columns = [customer_column, "total_sales"]
    customer_sales = customer_sales.sort_values("total_sales", ascending=False)
    
    # Identify VIP customers
    vip_threshold = customer_sales["total_sales"].quantile(1 - top_percentile)
    vip_customers = customer_sales[customer_sales["total_sales"] >= vip_threshold]
    
    # Find VIP customers with late deliveries
    late_orders_by_customer = (
        df[df[late_column] == True]
        .groupby(customer_column)
        .size()
        .reset_index(name="late_orders_count")
    )
    
    # Merge with VIP customers
    vip_at_risk = vip_customers.merge(
        late_orders_by_customer,
        on=customer_column,
        how="inner"
    )
    
    return vip_at_risk.sort_values("late_orders_count", ascending=False)


def export_to_parquet(
    df: pd.DataFrame,
    file_path: str,
    compression: str = "snappy"
) -> str:
    """
    Export DataFrame to Parquet format (optimized for Power BI).
    
    Args:
        df: DataFrame to export
        file_path: Output file path
        compression: Compression algorithm (default: snappy)
    
    Returns:
        str: Path to exported file
    """
    # Ensure directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Export to Parquet
    df.to_parquet(file_path, compression=compression, index=False)
    
    # Get file size
    file_size = get_file_size_mb(file_path)
    
    return file_path


def export_to_csv(
    df: pd.DataFrame,
    file_path: str,
    encoding: str = "utf-8"
) -> str:
    """
    Export DataFrame to CSV format.
    
    Args:
        df: DataFrame to export
        file_path: Output file path
        encoding: File encoding (default: utf-8)
    
    Returns:
        str: Path to exported file
    """
    # Ensure directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Export to CSV
    df.to_csv(file_path, index=False, encoding=encoding)
    
    # Get file size
    file_size = get_file_size_mb(file_path)
    
    return file_path


def generate_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive data profile.
    
    Args:
        df: DataFrame to profile
    
    Returns:
        dict: Data profile information
    """
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isnull().sum().to_dict(),
        "null_percentages": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "memory_mb": get_dataframe_memory_mb(df),
        "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical_columns": df.select_dtypes(include=["object"]).columns.tolist(),
        "datetime_columns": df.select_dtypes(include=["datetime"]).columns.tolist(),
    }
    
    # Add basic statistics for numeric columns
    if profile["numeric_columns"]:
        numeric_stats = df[profile["numeric_columns"]].describe().to_dict()
        profile["numeric_stats"] = numeric_stats
    
    return profile


def print_data_profile(profile: Dict[str, Any]):
    """
    Print data profile in readable format.
    
    Args:
        profile: Data profile dictionary
    """
    print("\n" + "=" * 70)
    print("DATA PROFILE")
    print("=" * 70)
    print(f"Rows: {profile['row_count']:,}")
    print(f"Columns: {profile['column_count']}")
    print(f"Memory: {profile['memory_mb']:.2f} MB")
    print(f"\nNumeric columns: {len(profile['numeric_columns'])}")
    print(f"Categorical columns: {len(profile['categorical_columns'])}")
    print(f"DateTime columns: {len(profile['datetime_columns'])}")
    
    # Print columns with high null percentage
    high_nulls = {
        col: pct for col, pct in profile["null_percentages"].items()
        if pct > 10
    }
    if high_nulls:
        print("\nColumns with >10% nulls:")
        for col, pct in high_nulls.items():
            print(f"  {col}: {pct:.1f}%")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test utilities
    print("Testing ETL utilities...")
    
    # Test column sanitization
    test_columns = ["Customer ID", "Order Date (DateOrders)", "Sales per customer"]
    print("\nColumn sanitization:")
    for col in test_columns:
        print(f"  '{col}' -> '{sanitize_column_name(col)}'")
    
    # Test duration formatting
    print("\nDuration formatting:")
    test_durations = [45, 125, 3665, 7325]
    for duration in test_durations:
        print(f"  {duration}s -> {format_duration(duration)}")
