#!/usr/bin/env python3
"""
Torre Control - Data Extraction Module
=======================================

Handles extraction of raw data from CSV files and other sources.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import get_settings
from src.logging_config import LoggerMixin, log_execution_time


class DataExtractor(LoggerMixin):
    """
    Extracts data from various sources (CSV, database, API).
    
    Handles encoding issues, chunking for large files, and error recovery.
    """
    
    def __init__(self):
        """Initialize DataExtractor."""
        self.settings = get_settings()
        self.logger.info("DataExtractor initialized")
    
    @log_execution_time
    def extract_csv(
        self,
        file_path: Optional[str] = None,
        encoding: str = "ISO-8859-1",
        chunksize: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Extract data from CSV file.
        
        Args:
            file_path: Path to CSV file (default: from settings)
            encoding: File encoding (default: ISO-8859-1 for DataCo dataset)
            chunksize: Number of rows per chunk for large files
        
        Returns:
            pd.DataFrame: Extracted data
        
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            pd.errors.ParserError: If CSV parsing fails
        """
        # Use default path from settings if not provided
        csv_path = file_path or self.settings.csv_file_path
        
        # Resolve path relative to project root
        if not os.path.isabs(csv_path):
            csv_path = str(self.settings.project_root / csv_path)
        
        self.logger.info(f"Extracting CSV from: {csv_path}")
        
        # Check if file exists
        if not os.path.exists(csv_path):
            self.logger.error(f"CSV file not found: {csv_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Get file size for logging
        file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
        self.logger.info(f"File size: {file_size_mb:.2f} MB")
        
        try:
            # Read CSV with specified encoding
            if chunksize:
                self.logger.info(f"Reading CSV in chunks of {chunksize} rows")
                chunks = []
                for i, chunk in enumerate(pd.read_csv(csv_path, encoding=encoding, chunksize=chunksize)):
                    chunks.append(chunk)
                    if (i + 1) % 10 == 0:
                        self.logger.debug(f"Processed {(i + 1) * chunksize} rows")
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_csv(csv_path, encoding=encoding)
            
            self.logger.info(f"Successfully extracted {len(df):,} rows, {len(df.columns)} columns")
            
            # Log basic statistics
            memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            self.logger.debug(f"DataFrame memory usage: {memory_mb:.2f} MB")
            
            return df
            
        except pd.errors.ParserError as e:
            self.logger.error(f"CSV parsing error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error reading CSV: {e}")
            raise
    
    def sanitize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sanitize column names for database compatibility.
        
        - Convert to lowercase
        - Replace spaces with underscores
        - Remove special characters except underscores
        
        Args:
            df: DataFrame with raw column names
        
        Returns:
            pd.DataFrame: DataFrame with sanitized column names
        """
        self.logger.info("Sanitizing column names")
        
        original_columns = df.columns.tolist()
        
        # Sanitize column names
        new_columns = []
        for col in df.columns:
            # Convert to lowercase and replace spaces with underscores
            sanitized = col.lower().replace(" ", "_").replace("(", "").replace(")", "")
            # Remove other special characters except underscores
            sanitized = "".join(c if c.isalnum() or c == "_" else "" for c in sanitized)
            # Remove leading/trailing underscores and collapse multiple underscores
            sanitized = "_".join(filter(None, sanitized.split("_")))
            new_columns.append(sanitized)
        
        # Apply new column names
        df.columns = new_columns
        
        # Log changes
        for old, new in zip(original_columns, new_columns):
            if old != new:
                self.logger.debug(f"Column renamed: '{old}' -> '{new}'")
        
        self.logger.info(f"Sanitized {len(new_columns)} column names")
        
        return df
    
    def extract_and_sanitize(
        self,
        file_path: Optional[str] = None,
        encoding: str = "ISO-8859-1"
    ) -> pd.DataFrame:
        """
        Extract CSV and sanitize column names in one step.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding
        
        Returns:
            pd.DataFrame: Extracted and sanitized data
        """
        df = self.extract_csv(file_path=file_path, encoding=encoding)
        df = self.sanitize_column_names(df)
        return df
    
    def get_data_profile(self, df: pd.DataFrame) -> dict:
        """
        Get basic profile of the dataset.
        
        Args:
            df: DataFrame to profile
        
        Returns:
            dict: Profile information
        """
        profile = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "null_percentages": (df.isnull().sum() / len(df) * 100).to_dict(),
            "memory_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
        }
        
        self.logger.info(
            f"Data profile: {profile['row_count']:,} rows, "
            f"{profile['column_count']} columns, "
            f"{profile['memory_mb']:.2f} MB"
        )
        
        # Log columns with high null percentage
        high_nulls = {
            col: pct for col, pct in profile["null_percentages"].items()
            if pct > 10
        }
        if high_nulls:
            self.logger.warning(
                f"Columns with >10% nulls: {', '.join(f'{col}({pct:.1f}%)' for col, pct in high_nulls.items())}"
            )
        
        return profile


if __name__ == "__main__":
    # Test extraction
    extractor = DataExtractor()
    
    # Test with sample CSV (adjust path as needed)
    try:
        df = extractor.extract_and_sanitize()
        profile = extractor.get_data_profile(df)
        print(f"\nExtracted {profile['row_count']:,} rows")
        print(f"Sample columns: {profile['columns'][:5]}")
    except FileNotFoundError:
        print("CSV file not found. Configure correct path in .env")
