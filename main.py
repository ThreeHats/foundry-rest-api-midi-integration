import sys
import logging
import argparse
from PyQt6.QtWidgets import QApplication
from app import MidiRestApp
from logging_config import setup_logging

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MIDI to REST API Integration")
    parser.add_argument("--dev", action="store_true", help="Enable development mode with detailed logging")
    args = parser.parse_args()
    
    # Setup logging based on mode
    if args.dev:
        setup_logging(logging.DEBUG)
        logger = logging.getLogger("main")
        logger.info("Development mode enabled with detailed logging")
    else:
        # In production mode, only log warnings and errors
        setup_logging(logging.WARNING)
        logger = logging.getLogger("main")
    
    try:
        logger.info("Starting application")
        app = QApplication(sys.argv)
        window = MidiRestApp(dev_mode=args.dev)
        window.show()
        logger.info("Application UI displayed")
        sys.exit(app.exec())
    except Exception as e:
        if args.dev:
            logger.critical("Unhandled exception: %s", str(e), exc_info=True)
        else:
            # In production, don't include full traceback
            logger.error("Error: %s", str(e))
        raise
