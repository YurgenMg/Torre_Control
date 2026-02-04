#!/usr/bin/env python3
"""
Torre Control - Data Validation Module
=======================================

Provides data quality validation checks for ETL pipeline.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.config import get_settings
from src.etl.load import DataLoader
from src.logging_config import LoggerMixin


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class DataValidator(LoggerMixin):
    """
    Validates data quality throughout ETL pipeline.
    
    Checks for nulls, outliers, referential integrity, and business rules.
    """
    
    def __init__(self, loader: Optional[DataLoader] = None):
        """
        Initialize DataValidator.
        
        Args:
            loader: DataLoader instance (creates new if not provided)
        """
        self.settings = get_settings()
        self.loader = loader or DataLoader()
        self.validation_results = []
        self.logger.info("DataValidator initialized")
    
    def _add_result(
        self,
        check_name: str,
        passed: bool,
        message: str,
        severity: str = "ERROR"
    ):
        """
        Add validation result.
        
        Args:
            check_name: Name of the validation check
            passed: Whether check passed
            message: Result message
            severity: Severity level (ERROR, WARNING, INFO)
        """
        result = {
            "check": check_name,
            "passed": passed,
            "message": message,
            "severity": severity
        }
        self.validation_results.append(result)
        
        if passed:
            self.logger.info(f"✅ {check_name}: {message}")
        elif severity == "ERROR":
            self.logger.error(f"❌ {check_name}: {message}")
        else:
            self.logger.warning(f"⚠️  {check_name}: {message}")
    
    def validate_table_exists(self, table_name: str, schema: str = "dw") -> bool:
        """
        Validate that a table exists.
        
        Args:
            table_name: Table name
            schema: Schema name
        
        Returns:
            bool: True if table exists
        """
        exists = self.loader.table_exists(table_name, schema)
        
        self._add_result(
            f"table_exists_{table_name}",
            exists,
            f"Table {schema}.{table_name} {'exists' if exists else 'does not exist'}",
            "ERROR" if not exists else "INFO"
        )
        
        return exists
    
    def validate_row_count(
        self,
        table_name: str,
        schema: str = "dw",
        min_rows: int = 1
    ) -> Tuple[bool, int]:
        """
        Validate that a table has minimum number of rows.
        
        Args:
            table_name: Table name
            schema: Schema name
            min_rows: Minimum expected rows
        
        Returns:
            Tuple[bool, int]: (passed, actual_count)
        """
        try:
            count = self.loader.get_table_count(table_name, schema)
            passed = count >= min_rows
            
            self._add_result(
                f"row_count_{table_name}",
                passed,
                f"{schema}.{table_name} has {count:,} rows (minimum: {min_rows:,})",
                "ERROR" if not passed else "INFO"
            )
            
            return passed, count
        except Exception as e:
            self._add_result(
                f"row_count_{table_name}",
                False,
                f"Failed to get row count: {e}",
                "ERROR"
            )
            return False, 0
    
    def validate_no_nulls(
        self,
        table_name: str,
        columns: List[str],
        schema: str = "dw"
    ) -> bool:
        """
        Validate that specified columns have no NULL values.
        
        Args:
            table_name: Table name
            columns: List of column names to check
            schema: Schema name
        
        Returns:
            bool: True if no NULLs found
        """
        all_passed = True
        
        for column in columns:
            query = f"""
                SELECT COUNT(*) as null_count
                FROM {schema}.{table_name}
                WHERE {column} IS NULL
            """
            
            try:
                result = self.loader.execute_query(query)
                null_count = result["null_count"].iloc[0]
                passed = null_count == 0
                
                self._add_result(
                    f"no_nulls_{table_name}_{column}",
                    passed,
                    f"{schema}.{table_name}.{column} has {null_count:,} NULL values",
                    "ERROR" if not passed else "INFO"
                )
                
                all_passed = all_passed and passed
                
            except Exception as e:
                self._add_result(
                    f"no_nulls_{table_name}_{column}",
                    False,
                    f"Failed to check NULLs: {e}",
                    "ERROR"
                )
                all_passed = False
        
        return all_passed
    
    def validate_referential_integrity(
        self,
        fact_table: str,
        fact_column: str,
        dim_table: str,
        dim_column: str,
        schema: str = "dw"
    ) -> bool:
        """
        Validate referential integrity between fact and dimension tables.
        
        Args:
            fact_table: Fact table name
            fact_column: Foreign key column in fact table
            dim_table: Dimension table name
            dim_column: Primary key column in dimension table
            schema: Schema name
        
        Returns:
            bool: True if all foreign keys exist in dimension
        """
        query = f"""
            SELECT COUNT(*) as orphan_count
            FROM {schema}.{fact_table} f
            LEFT JOIN {schema}.{dim_table} d ON f.{fact_column} = d.{dim_column}
            WHERE f.{fact_column} IS NOT NULL
              AND d.{dim_column} IS NULL
        """
        
        try:
            result = self.loader.execute_query(query)
            orphan_count = result["orphan_count"].iloc[0]
            passed = orphan_count == 0
            
            self._add_result(
                f"referential_integrity_{fact_table}_{dim_table}",
                passed,
                f"Found {orphan_count:,} orphaned records in {fact_table}.{fact_column}",
                "ERROR" if not passed else "INFO"
            )
            
            return passed
            
        except Exception as e:
            self._add_result(
                f"referential_integrity_{fact_table}_{dim_table}",
                False,
                f"Failed to check referential integrity: {e}",
                "ERROR"
            )
            return False
    
    def validate_otif_calculation(self, schema: str = "dw") -> bool:
        """
        Validate OTIF (On-Time In-Full) calculation logic.
        
        Args:
            schema: Schema name
        
        Returns:
            bool: True if OTIF calculation is valid
        """
        query = f"""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN is_late = FALSE AND is_complete = TRUE THEN 1 ELSE 0 END) as otif_orders,
                ROUND(
                    100.0 * SUM(CASE WHEN is_late = FALSE AND is_complete = TRUE THEN 1 ELSE 0 END) / 
                    NULLIF(COUNT(*), 0), 
                    2
                ) as otif_percentage
            FROM {schema}.fact_orders
            WHERE is_canceled = FALSE
        """
        
        try:
            result = self.loader.execute_query(query)
            
            total = result["total_orders"].iloc[0]
            otif_orders = result["otif_orders"].iloc[0]
            otif_pct = result["otif_percentage"].iloc[0]
            
            passed = otif_pct is not None and 0 <= otif_pct <= 100
            
            self._add_result(
                "otif_calculation",
                passed,
                f"OTIF: {otif_pct}% ({otif_orders:,} of {total:,} orders)",
                "INFO"
            )
            
            # Check if OTIF is below target
            if otif_pct < self.settings.otif_target:
                self._add_result(
                    "otif_target",
                    False,
                    f"OTIF {otif_pct}% is below target {self.settings.otif_target}%",
                    "WARNING"
                )
            
            return passed
            
        except Exception as e:
            self._add_result(
                "otif_calculation",
                False,
                f"Failed to calculate OTIF: {e}",
                "ERROR"
            )
            return False
    
    def validate_all(self) -> Dict[str, any]:
        """
        Run all validation checks.
        
        Returns:
            dict: Validation summary
        """
        self.logger.info("Starting comprehensive validation checks...")
        self.validation_results = []
        
        # Check that all tables exist
        tables = ["stg_raw_orders", "dim_customer", "dim_product", "dim_geography", "dim_date", "fact_orders"]
        for table in tables:
            self.validate_table_exists(table)
        
        # Check row counts
        self.validate_row_count("stg_raw_orders", min_rows=1000)
        self.validate_row_count("dim_customer", min_rows=100)
        self.validate_row_count("dim_product", min_rows=10)
        self.validate_row_count("dim_geography", min_rows=5)
        self.validate_row_count("dim_date", min_rows=30)
        self.validate_row_count("fact_orders", min_rows=1000)
        
        # Check for NULLs in critical columns
        self.validate_no_nulls("fact_orders", ["order_id", "order_item_id", "customer_id"])
        self.validate_no_nulls("dim_customer", ["customer_id"])
        self.validate_no_nulls("dim_product", ["product_card_id"])
        
        # Check referential integrity
        self.validate_referential_integrity("fact_orders", "customer_id", "dim_customer", "customer_id")
        self.validate_referential_integrity("fact_orders", "product_card_id", "dim_product", "product_card_id")
        self.validate_referential_integrity("fact_orders", "date_key", "dim_date", "date_key")
        self.validate_referential_integrity("fact_orders", "geography_key", "dim_geography", "geography_key")
        
        # Business rule validations
        self.validate_otif_calculation()
        
        # Summarize results
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for r in self.validation_results if r["passed"])
        failed_checks = total_checks - passed_checks
        
        summary = {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "success_rate": round(100 * passed_checks / total_checks, 2) if total_checks > 0 else 0,
            "results": self.validation_results
        }
        
        self.logger.info(
            f"Validation complete: {passed_checks}/{total_checks} checks passed "
            f"({summary['success_rate']}%)"
        )
        
        return summary
    
    def print_summary(self):
        """Print validation summary to console."""
        print("\n" + "=" * 70)
        print("DATA VALIDATION SUMMARY")
        print("=" * 70)
        
        for result in self.validation_results:
            icon = "✅" if result["passed"] else "❌" if result["severity"] == "ERROR" else "⚠️ "
            print(f"{icon} [{result['severity']}] {result['check']}: {result['message']}")
        
        total = len(self.validation_results)
        passed = sum(1 for r in self.validation_results if r["passed"])
        
        print("=" * 70)
        print(f"Total: {passed}/{total} checks passed")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test validator
    validator = DataValidator()
    
    try:
        summary = validator.validate_all()
        validator.print_summary()
        
        if summary["failed"] > 0:
            print(f"\n⚠️  {summary['failed']} validation checks failed")
    except Exception as e:
        print(f"Validation failed: {e}")
