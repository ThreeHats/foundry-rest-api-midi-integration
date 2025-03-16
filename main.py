import sys
import logging
from PyQt6.QtWidgets import QApplication
from app import MidiRestApp
from logging_config import setup_logging

if __name__ == "__main__":
    # Setup logging before anything else (DEBUG for development, INFO for production)
    setup_logging(logging.DEBUG)
    logger = logging.getLogger("main")
    
    try:
        logger.info("Starting application")
        app = QApplication(sys.argv)
        window = MidiRestApp()
        window.show()
        logger.info("Application UI displayed")
        sys.exit(app.exec())
    except Exception as e:
        logger.critical("Unhandled exception: %s", str(e), exc_info=True)
        raise
