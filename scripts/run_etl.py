#!/usr/bin/env python3
"""
Torre Control - ETL Pipeline Orchestrator
==========================================

Main orchestration script for complete ETL pipeline execution.
Coordinates extraction, transformation, loading, and validation.

Usage:
    python scripts/run_etl.py [--skip-extract] [--skip-transform] [--skip-validate]

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.etl.extract import DataExtractor
from src.etl.load import DataLoader
from src.etl.transform import DataTransformer
from src.etl.validate import DataValidator
from src.logging_config import get_logger


class ETLOrchestrator:
    """
    Orchestrates the complete ETL pipeline.
    
    Coordinates all ETL steps with proper error handling and logging.
    """
    
    def __init__(self):
        """Initialize ETL orchestrator."""
        self.settings = get_settings()
        self.logger = get_logger("ETLOrchestrator")
        self.start_time = datetime.now()
        
        # Initialize ETL components
        self.extractor = DataExtractor()
        self.loader = DataLoader()
        self.transformer = DataTransformer(loader=self.loader)
        self.validator = DataValidator(loader=self.loader)
        
        self.logger.info("=" * 70)
        self.logger.info("TORRE CONTROL - ETL PIPELINE ORCHESTRATOR")
        self.logger.info("=" * 70)
        self.logger.info(f"Environment: {self.settings.environment}")
        self.logger.info(f"Database: {self.settings.database_url.split('@')[1]}")
        self.logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 70)
    
    def extract_stage(self) -> bool:
        """
        Execute extraction stage.
        
        Returns:
            bool: True if successful
        """
        self.logger.info("\n[STAGE 1/4] EXTRACT - Loading raw data from CSV")
        self.logger.info("-" * 70)
        
        try:
            # Extract and sanitize data
            df = self.extractor.extract_and_sanitize()
            
            # Load into staging table
            self.loader.load_dataframe(
                df=df,
                table_name="stg_raw_orders",
                schema="dw",
                if_exists="replace"
            )
            
            self.logger.info("✅ Extract stage completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Extract stage failed: {e}")
            return False
    
    def transform_stage(self) -> bool:
        """
        Execute transformation stage.
        
        Returns:
            bool: True if successful
        """
        self.logger.info("\n[STAGE 2/4] TRANSFORM - Creating star schema")
        self.logger.info("-" * 70)
        
        try:
            # Execute all transformations
            results = self.transformer.transform_all()
            
            # Log results
            self.logger.info("Transformation results:")
            for table, count in results.items():
                self.logger.info(f"  {table}: {count:,} rows")
            
            self.logger.info("✅ Transform stage completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Transform stage failed: {e}")
            return False
    
    def validate_stage(self) -> bool:
        """
        Execute validation stage.
        
        Returns:
            bool: True if all validations passed
        """
        self.logger.info("\n[STAGE 3/4] VALIDATE - Data quality checks")
        self.logger.info("-" * 70)
        
        try:
            # Run all validations
            summary = self.validator.validate_all()
            
            # Print summary
            self.validator.print_summary()
            
            # Check if validation passed
            if summary["failed"] > 0:
                self.logger.warning(
                    f"⚠️  Validation completed with {summary['failed']} failures "
                    f"(success rate: {summary['success_rate']}%)"
                )
                return False
            
            self.logger.info("✅ Validate stage completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Validate stage failed: {e}")
            return False
    
    def export_stage(self) -> bool:
        """
        Execute export stage.
        
        Returns:
            bool: True if successful
        """
        self.logger.info("\n[STAGE 4/4] EXPORT - Exporting data for Power BI")
        self.logger.info("-" * 70)
        
        try:
            # Ensure processed data directory exists
            self.settings.ensure_directories()
            
            # Export each table as CSV
            tables = {
                "dim_customer": "dim_customer.csv",
                "dim_product": "dim_product.csv",
                "dim_geography": "dim_geography.csv",
                "dim_date": "dim_date.csv",
                "fact_orders": "fact_orders.csv"
            }
            
            for table, filename in tables.items():
                self.logger.info(f"Exporting {table}...")
                
                # Query data
                query = f"SELECT * FROM dw.{table}"
                df = self.loader.execute_query(query)
                
                # Export to CSV
                output_path = self.settings.data_processed_dir / filename
                df.to_csv(output_path, index=False)
                
                self.logger.info(f"  ✅ {filename}: {len(df):,} rows")
            
            self.logger.info("✅ Export stage completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Export stage failed: {e}")
            return False
    
    def run(
        self,
        skip_extract: bool = False,
        skip_transform: bool = False,
        skip_validate: bool = False,
        skip_export: bool = False
    ) -> bool:
        """
        Run complete ETL pipeline.
        
        Args:
            skip_extract: Skip extraction stage
            skip_transform: Skip transformation stage
            skip_validate: Skip validation stage
            skip_export: Skip export stage
        
        Returns:
            bool: True if pipeline completed successfully
        """
        try:
            # Stage 1: Extract
            if not skip_extract:
                if not self.extract_stage():
                    return False
            else:
                self.logger.info("\n[STAGE 1/4] EXTRACT - SKIPPED")
            
            # Stage 2: Transform
            if not skip_transform:
                if not self.transform_stage():
                    return False
            else:
                self.logger.info("\n[STAGE 2/4] TRANSFORM - SKIPPED")
            
            # Stage 3: Validate
            validation_passed = True
            if not skip_validate:
                validation_passed = self.validate_stage()
            else:
                self.logger.info("\n[STAGE 3/4] VALIDATE - SKIPPED")
            
            # Stage 4: Export
            if not skip_export:
                if not self.export_stage():
                    return False
            else:
                self.logger.info("\n[STAGE 4/4] EXPORT - SKIPPED")
            
            # Calculate execution time
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            # Final summary
            self.logger.info("\n" + "=" * 70)
            self.logger.info("PIPELINE EXECUTION SUMMARY")
            self.logger.info("=" * 70)
            self.logger.info(f"Status: {'SUCCESS ✅' if validation_passed else 'COMPLETED WITH WARNINGS ⚠️ '}")
            self.logger.info(f"Duration: {elapsed:.2f} seconds")
            self.logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 70)
            
            if not validation_passed:
                self.logger.warning(
                    "\n⚠️  Pipeline completed but validation checks failed. "
                    "Review logs for details."
                )
            
            return validation_passed
            
        except KeyboardInterrupt:
            self.logger.warning("\n⚠️  Pipeline interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"\n❌ Pipeline failed with unexpected error: {e}")
            return False
        finally:
            # Cleanup
            self.loader.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Torre Control ETL Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python scripts/run_etl.py
  
  # Skip extraction (use existing staging data)
  python scripts/run_etl.py --skip-extract
  
  # Run only transformation
  python scripts/run_etl.py --skip-extract --skip-validate --skip-export
        """
    )
    
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Skip extraction stage (use existing staging data)"
    )
    
    parser.add_argument(
        "--skip-transform",
        action="store_true",
        help="Skip transformation stage"
    )
    
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip validation stage"
    )
    
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Skip export stage"
    )
    
    args = parser.parse_args()
    
    # Initialize and run orchestrator
    orchestrator = ETLOrchestrator()
    success = orchestrator.run(
        skip_extract=args.skip_extract,
        skip_transform=args.skip_transform,
        skip_validate=args.skip_validate,
        skip_export=args.skip_export
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
