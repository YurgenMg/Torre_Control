#!/usr/bin/env python3
"""
Torre Control - Centralized Logging Configuration
==================================================

Provides consistent logging across all ETL modules with file and console handlers.

Author: Torre Control Engineering Team
Date: 2026-02-04
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import get_settings


def setup_logging(
    name: Optional[str] = None,
    log_file: Optional[str] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    
    Args:
        name: Logger name (default: __name__ of caller)
        log_file: Log file name (default: etl.log)
        level: Logging level (default: from settings)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    settings = get_settings()
    
    # Ensure logs directory exists
    settings.ensure_directories()
    
    # Get logger
    logger_name = name or "torre_control"
    logger = logging.getLogger(logger_name)
    
    # Set log level
    log_level = getattr(logging, level or settings.log_level)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # File handler
    log_file_path = settings.logs_dir / (log_file or "etl.log")
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with standard configuration.
    
    Args:
        name: Logger name (default: torre_control)
    
    Returns:
        logging.Logger: Logger instance
    """
    return setup_logging(name=name)


class LoggerMixin:
    """
    Mixin class to add logging capability to any class.
    
    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("This is a log message")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_execution_time(func):
    """
    Decorator to log function execution time.
    
    Usage:
        @log_execution_time
        def my_function():
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()
        logger.info(f"Starting {func.__name__}...")
        
        try:
            result = func(*args, **kwargs)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed {func.__name__} in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed {func.__name__} after {elapsed:.2f}s: {e}")
            raise
    
    return wrapper


if __name__ == "__main__":
    # Test logging configuration
    logger = setup_logging("test_logger")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test decorator
    @log_execution_time
    def test_function():
        import time
        time.sleep(0.1)
        return "Success"
    
    result = test_function()
    print(f"Result: {result}")
