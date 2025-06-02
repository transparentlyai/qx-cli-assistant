import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Optional # Added this import

logger = logging.getLogger("qx")

# Global variable to hold the temporary stream handler
temp_stream_handler: Optional[logging.Handler] = None

def configure_logging():
    """
    Configures the application's logging based on QX_LOG_LEVEL environment variable.
    Initially logs to file and console (for INFO and above). Console logging for INFO
    will be redirected to Textual RichLog once the app starts.
    """
    global temp_stream_handler

    log_level_name = os.getenv("QX_LOG_LEVEL", "ERROR").upper()  # Default to INFO
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    effective_log_level = LOG_LEVELS.get(log_level_name, logging.ERROR)

    # Create log file in ~/tmp directory
    log_dir = Path.home() / "tmp"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "qx.log"

    # Clear existing handlers to prevent duplicates on re-configuration
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    # Add a temporary StreamHandler for INFO and above, to be removed later
    temp_stream_handler = logging.StreamHandler()
    temp_stream_handler.setLevel(effective_log_level)
    temp_stream_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(temp_stream_handler)

    # Ensure critical errors always go to stderr
    critical_stream_handler = logging.StreamHandler(sys.stderr)
    critical_stream_handler.setLevel(logging.CRITICAL)
    critical_stream_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    logger.addHandler(critical_stream_handler)

    logger.setLevel(effective_log_level)

    # Set up global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )
        # Also write to file directly in case logger fails
        with open(log_file, "a") as f:
            f.write(f"\n=== UNCAUGHT EXCEPTION ===\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            f.write(f"=== END EXCEPTION ===\n\n")

    sys.excepthook = handle_exception

    logger.debug(
        f"QX application log level set to: {logging.getLevelName(effective_log_level)} ({effective_log_level})"
    )
    logger.debug(f"Logging to file: {log_file}")
    logger.debug("Global exception handler installed")

def remove_temp_stream_handler():
    global temp_stream_handler
    if temp_stream_handler and temp_stream_handler in logger.handlers:
        logger.removeHandler(temp_stream_handler)
        temp_stream_handler = None
