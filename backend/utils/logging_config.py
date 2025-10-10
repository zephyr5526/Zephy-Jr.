"""
Logging configuration for the application
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Setup application logging configuration"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                log_dir / f"zephy-jr-{datetime.now().strftime('%Y-%m-%d')}.log",
                encoding='utf-8'
            )
        ]
    )
    
    # Configure specific loggers
    loggers = {
        'uvicorn': logging.INFO,
        'uvicorn.access': logging.INFO,
        'fastapi': logging.INFO,
        'sqlalchemy.engine': logging.WARNING,
        'sqlalchemy.pool': logging.WARNING,
        'zephy_jr': logging.DEBUG
    }
    
    for logger_name, level in loggers.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Create main application logger
    logger = logging.getLogger("zephy_jr")
    logger.info("🚀 Zephy Jr. Control Panel logging initialized")
    
    return logger