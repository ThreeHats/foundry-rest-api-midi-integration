import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration for the entire application.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.expanduser('~'), '.foundry_midi_rest', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Get today's date for log filename
    date_str = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'midi_rest_{date_str}.log')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates if setup_logging is called multiple times
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(name)-25s | %(message)s'
    )
    
    # File handler (rotating log)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Add both handlers to logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup information
    logging.info("=" * 80)
    logging.info("MIDI to REST API application starting")
    logging.info("Log level: %s", logging.getLevelName(log_level))
    logging.info("Log file: %s", log_file)
    logging.info("=" * 80)
    
    return root_logger

def get_logger(name):
    """
    Get a named logger for a specific module.
    """
    return logging.getLogger(name)
