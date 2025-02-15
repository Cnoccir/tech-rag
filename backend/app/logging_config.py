# app/logging_config.py
import logging
import sys
from logging.config import dictConfig
from typing import Dict, Any

def setup_logging():
    """Setup logging configuration"""
    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
                "level": "DEBUG",
            },
            "access": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "access",
                "level": "INFO",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "default",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "app": {  # Our application logger
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {  # Root logger
            "handlers": ["console"],
            "level": "INFO",
        },
    }

    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)

    # Apply the configuration
    dictConfig(log_config)
