#!/usr/bin/env python3
"""
Torre Control - Configuration Management
=========================================

Centralized configuration using Pydantic for settings validation.
Loads configuration from environment variables with sensible defaults.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        postgres_user: PostgreSQL username
        postgres_password: PostgreSQL password
        postgres_host: PostgreSQL host
        postgres_port: PostgreSQL port
        postgres_db: PostgreSQL database name
        database_url: Full PostgreSQL connection string (auto-generated)
        environment: Application environment (development/production)
        log_level: Logging level (DEBUG/INFO/WARNING/ERROR)
        csv_file_path: Path to raw CSV data file
        staging_table: Staging table name
        batch_size: Batch size for data loading
        otif_target: Target OTIF percentage
        revenue_at_risk_threshold: Alert threshold for revenue at risk
        churn_risk_ltv_threshold: VIP customer LTV threshold
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # PostgreSQL Configuration
    postgres_user: str = Field(default="admin", description="PostgreSQL username")
    postgres_password: str = Field(default="adminpassword", description="PostgreSQL password")
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5433, description="PostgreSQL port")
    postgres_db: str = Field(default="supply_chain_dw", description="PostgreSQL database")
    
    # Application Configuration
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Data Loading Configuration
    csv_file_path: str = Field(
        default="data/raw/DataCoSupplyChainDataset.csv",
        description="Path to raw CSV file"
    )
    staging_table: str = Field(default="dw.stg_raw_orders", description="Staging table")
    batch_size: int = Field(default=1000, description="Batch size for loading")
    
    # Analytics Configuration
    otif_target: float = Field(default=95.0, description="Target OTIF percentage")
    revenue_at_risk_threshold: float = Field(
        default=1000000.0,
        description="Revenue at risk alert threshold"
    )
    churn_risk_ltv_threshold: float = Field(
        default=50000.0,
        description="VIP customer LTV threshold"
    )
    
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "production", "staging", "test"]
        if v.lower() not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v.lower()
    
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent
    
    @property
    def data_raw_dir(self) -> Path:
        """Get raw data directory."""
        return self.project_root / "data" / "raw"
    
    @property
    def data_processed_dir(self) -> Path:
        """Get processed data directory."""
        return self.project_root / "data" / "processed"
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory."""
        return self.project_root / "logs"
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        self.data_processed_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings: Application settings
    """
    return settings


if __name__ == "__main__":
    # Test configuration loading
    config = get_settings()
    print(f"Environment: {config.environment}")
    print(f"Database URL: {config.database_url}")
    print(f"Log Level: {config.log_level}")
    print(f"CSV Path: {config.csv_file_path}")
    print(f"Project Root: {config.project_root}")
