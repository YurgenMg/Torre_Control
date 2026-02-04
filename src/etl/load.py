#!/usr/bin/env python3
"""
Torre Control - Data Loading Module
====================================

Handles loading data into PostgreSQL database with batching and error handling.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from src.config import get_settings
from src.logging_config import LoggerMixin, log_execution_time


class DataLoader(LoggerMixin):
    """
    Loads data into PostgreSQL database.
    
    Handles connection management, batching, and error recovery.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize DataLoader.
        
        Args:
            database_url: PostgreSQL connection string (default: from settings)
        """
        self.settings = get_settings()
        self.database_url = database_url or self.settings.database_url
        self._engine: Optional[Engine] = None
        self.logger.info("DataLoader initialized")
    
    @property
    def engine(self) -> Engine:
        """
        Get or create SQLAlchemy engine.
        
        Returns:
            Engine: SQLAlchemy engine instance
        """
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    def _create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine with connection pooling.
        
        Returns:
            Engine: SQLAlchemy engine
        """
        self.logger.info(f"Creating database engine: {self.database_url.split('@')[1]}")
        
        try:
            engine = create_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.logger.info("Database connection established successfully")
            return engine
            
        except OperationalError as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            self.logger.info("Database connection test: SUCCESS")
            return True
        except Exception as e:
            self.logger.error(f"Database connection test: FAILED - {e}")
            return False
    
    def table_exists(self, table_name: str, schema: Optional[str] = None) -> bool:
        """
        Check if table exists in database.
        
        Args:
            table_name: Table name
            schema: Schema name (optional)
        
        Returns:
            bool: True if table exists
        """
        inspector = inspect(self.engine)
        
        if schema:
            exists = inspector.has_table(table_name, schema=schema)
        else:
            exists = inspector.has_table(table_name)
        
        self.logger.debug(
            f"Table {'exists' if exists else 'does not exist'}: "
            f"{schema + '.' if schema else ''}{table_name}"
        )
        
        return exists
    
    @log_execution_time
    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: Optional[str] = None,
        if_exists: str = "replace",
        chunksize: Optional[int] = None
    ) -> int:
        """
        Load DataFrame into PostgreSQL table.
        
        Args:
            df: DataFrame to load
            table_name: Target table name
            schema: Schema name (optional)
            if_exists: What to do if table exists ('fail', 'replace', 'append')
            chunksize: Rows per batch (default: from settings)
        
        Returns:
            int: Number of rows loaded
        """
        batch_size = chunksize or self.settings.batch_size
        
        full_table_name = f"{schema}.{table_name}" if schema else table_name
        self.logger.info(
            f"Loading {len(df):,} rows into {full_table_name} "
            f"(mode: {if_exists}, batch: {batch_size})"
        )
        
        try:
            # Load data in batches
            df.to_sql(
                name=table_name,
                con=self.engine,
                schema=schema,
                if_exists=if_exists,
                index=False,
                chunksize=batch_size,
                method="multi"  # Use multi-row INSERT for better performance
            )
            
            self.logger.info(f"Successfully loaded {len(df):,} rows into {full_table_name}")
            return len(df)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to load data into {full_table_name}: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query
            params: Query parameters (optional)
        
        Returns:
            pd.DataFrame: Query results
        """
        self.logger.debug(f"Executing query: {query[:100]}...")
        
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(text(query), conn, params=params)
            
            self.logger.info(f"Query returned {len(result):,} rows")
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_statement(self, statement: str, params: Optional[dict] = None) -> int:
        """
        Execute SQL statement (INSERT, UPDATE, DELETE, DDL).
        
        Args:
            statement: SQL statement
            params: Statement parameters (optional)
        
        Returns:
            int: Number of rows affected
        """
        self.logger.debug(f"Executing statement: {statement[:100]}...")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(statement), params or {})
                conn.commit()
                rows_affected = result.rowcount if hasattr(result, 'rowcount') else 0
            
            self.logger.info(f"Statement executed successfully (affected {rows_affected} rows)")
            return rows_affected
            
        except SQLAlchemyError as e:
            self.logger.error(f"Statement execution failed: {e}")
            raise
    
    def get_table_count(self, table_name: str, schema: Optional[str] = None) -> int:
        """
        Get row count for a table.
        
        Args:
            table_name: Table name
            schema: Schema name (optional)
        
        Returns:
            int: Number of rows
        """
        full_table = f"{schema}.{table_name}" if schema else table_name
        query = f"SELECT COUNT(*) as count FROM {full_table}"
        
        result = self.execute_query(query)
        count = result["count"].iloc[0]
        
        self.logger.info(f"Table {full_table} has {count:,} rows")
        return count
    
    def close(self):
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
            self.logger.info("Database connection closed")


if __name__ == "__main__":
    # Test loader
    loader = DataLoader()
    
    # Test connection
    if loader.test_connection():
        print("Database connection successful!")
        
        # Test query
        result = loader.execute_query("SELECT version()")
        print(f"PostgreSQL version: {result.iloc[0, 0]}")
