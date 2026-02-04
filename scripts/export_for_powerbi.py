#!/usr/bin/env python3
"""
Torre Control - Power BI Data Export Utility
=============================================

Exports processed data in Parquet format for optimal Power BI performance.

Usage:
    python scripts/export_for_powerbi.py [--format parquet|csv] [--tables table1,table2,...]

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.etl.load import DataLoader
from src.etl.utils import export_to_csv, export_to_parquet, get_file_size_mb
from src.logging_config import get_logger


class PowerBIExporter:
    """
    Exports data for Power BI consumption.
    
    Supports multiple formats with optimization for Power BI DirectQuery.
    """
    
    def __init__(self):
        """Initialize Power BI exporter."""
        self.settings = get_settings()
        self.logger = get_logger("PowerBIExporter")
        self.loader = DataLoader()
        
        # Ensure directories exist
        self.settings.ensure_directories()
        
        self.logger.info("=" * 70)
        self.logger.info("TORRE CONTROL - POWER BI DATA EXPORT UTILITY")
        self.logger.info("=" * 70)
    
    def export_table(
        self,
        table_name: str,
        schema: str = "dw",
        output_format: str = "parquet"
    ) -> Optional[str]:
        """
        Export a single table to specified format.
        
        Args:
            table_name: Table name to export
            schema: Schema name
            output_format: Output format (parquet or csv)
        
        Returns:
            str: Path to exported file, or None if failed
        """
        self.logger.info(f"Exporting {schema}.{table_name}...")
        
        try:
            # Query data from database
            query = f"SELECT * FROM {schema}.{table_name}"
            df = self.loader.execute_query(query)
            
            if len(df) == 0:
                self.logger.warning(f"  ⚠️  {table_name} is empty, skipping export")
                return None
            
            # Determine output path
            if output_format == "parquet":
                output_file = self.settings.data_processed_dir / f"{table_name}.parquet"
                export_to_parquet(df, str(output_file))
            else:
                output_file = self.settings.data_processed_dir / f"{table_name}.csv"
                export_to_csv(df, str(output_file))
            
            # Get file info
            file_size = get_file_size_mb(str(output_file))
            
            self.logger.info(
                f"  ✅ {table_name}: {len(df):,} rows, "
                f"{len(df.columns)} columns, {file_size:.2f} MB"
            )
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"  ❌ Failed to export {table_name}: {e}")
            return None
    
    def export_all(
        self,
        tables: Optional[List[str]] = None,
        output_format: str = "parquet"
    ) -> dict:
        """
        Export all dimension and fact tables.
        
        Args:
            tables: List of table names (default: all standard tables)
            output_format: Output format (parquet or csv)
        
        Returns:
            dict: Export results with file paths
        """
        self.logger.info(f"\nExporting data in {output_format.upper()} format...")
        self.logger.info("-" * 70)
        
        # Default tables to export
        if tables is None:
            tables = [
                "dim_customer",
                "dim_product",
                "dim_geography",
                "dim_date",
                "fact_orders"
            ]
        
        results = {}
        total_rows = 0
        total_size = 0.0
        
        for table in tables:
            output_path = self.export_table(table, output_format=output_format)
            results[table] = output_path
            
            if output_path:
                # Get stats
                file_size = get_file_size_mb(output_path)
                total_size += file_size
                
                # Count rows
                query = f"SELECT COUNT(*) as count FROM dw.{table}"
                count_df = self.loader.execute_query(query)
                total_rows += count_df["count"].iloc[0]
        
        # Summary
        self.logger.info("-" * 70)
        self.logger.info(f"Export Summary:")
        self.logger.info(f"  Tables exported: {len([p for p in results.values() if p])}/{len(tables)}")
        self.logger.info(f"  Total rows: {total_rows:,}")
        self.logger.info(f"  Total size: {total_size:.2f} MB")
        self.logger.info(f"  Output directory: {self.settings.data_processed_dir}")
        self.logger.info("-" * 70)
        
        return results
    
    def generate_connection_info(self):
        """
        Generate Power BI connection information.
        """
        self.logger.info("\n" + "=" * 70)
        self.logger.info("POWER BI CONNECTION INFORMATION")
        self.logger.info("=" * 70)
        self.logger.info("\n📊 Option 1: Import from Files (Recommended)")
        self.logger.info(f"  Location: {self.settings.data_processed_dir}")
        self.logger.info("  Files: dim_*.parquet/csv, fact_*.parquet/csv")
        self.logger.info("  Method: Get Data > Folder > Select processed directory")
        
        self.logger.info("\n🔗 Option 2: DirectQuery to Database")
        self.logger.info(f"  Server: {self.settings.postgres_host}:{self.settings.postgres_port}")
        self.logger.info(f"  Database: {self.settings.postgres_db}")
        self.logger.info("  Connection Mode: DirectQuery")
        self.logger.info("  Tables: dw.dim_*, dw.fact_*")
        
        self.logger.info("\n📝 Recommended Settings:")
        self.logger.info("  - Use Parquet for faster load times")
        self.logger.info("  - Enable incremental refresh for fact_orders")
        self.logger.info("  - Create relationships: fact_orders -> dim_* tables")
        self.logger.info("  - Set date table: dim_date (mark as date table)")
        
        self.logger.info("\n📚 For detailed guide:")
        self.logger.info("  See: docs/POWERBI_GUIDE.md")
        self.logger.info("=" * 70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export Torre Control data for Power BI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all tables as Parquet (recommended)
  python scripts/export_for_powerbi.py
  
  # Export as CSV
  python scripts/export_for_powerbi.py --format csv
  
  # Export specific tables only
  python scripts/export_for_powerbi.py --tables dim_customer,fact_orders
        """
    )
    
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Output format (default: parquet)"
    )
    
    parser.add_argument(
        "--tables",
        type=str,
        help="Comma-separated list of tables to export (default: all)"
    )
    
    parser.add_argument(
        "--show-connection-info",
        action="store_true",
        help="Show Power BI connection information"
    )
    
    args = parser.parse_args()
    
    # Parse tables list if provided
    tables = None
    if args.tables:
        tables = [t.strip() for t in args.tables.split(",")]
    
    # Initialize exporter
    exporter = PowerBIExporter()
    
    try:
        # Export data
        results = exporter.export_all(tables=tables, output_format=args.format)
        
        # Show connection info if requested
        if args.show_connection_info:
            exporter.generate_connection_info()
        
        # Check for failures
        failed = [t for t, p in results.items() if p is None]
        if failed:
            exporter.logger.error(f"\n❌ Failed to export: {', '.join(failed)}")
            sys.exit(1)
        
        exporter.logger.info("\n✅ Export completed successfully!")
        sys.exit(0)
        
    except KeyboardInterrupt:
        exporter.logger.warning("\n⚠️  Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        exporter.logger.error(f"\n❌ Export failed: {e}")
        sys.exit(1)
    finally:
        exporter.loader.close()


if __name__ == "__main__":
    main()
