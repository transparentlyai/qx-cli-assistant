import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Optional

logger = logging.getLogger("qx")

# Global variable to hold the temporary stream handler
temp_stream_handler: Optional[logging.Handler] = None


def configure_logging():
    """
    Configures the application's logging.

    - QX_LOG_LEVEL sets the logging level for all logs (qx and other libraries)
    - QX_LOG_FILE, if set, redirects all logs to the specified file and disables console output
    """
    global temp_stream_handler

    # Get log level from QX_LOG_LEVEL (always a level name)
    log_level_name = os.getenv("QX_LOG_LEVEL", "ERROR").upper()
    
    # Get log file path from QX_LOG_FILE (if set)
    log_file_path = os.getenv("QX_LOG_FILE")

    # Configure LiteLLM logging based on whether we're using file or console logging
    os.environ["LITELLM_LOG"] = log_level_name
    if log_file_path:
        # Disable LiteLLM's console logging when using file logging
        os.environ["LITELLM_LOG_LEVEL"] = (
            "CRITICAL"  # Suppress most LiteLLM console output
        )
        # Note: We'll still configure LiteLLM loggers to write to file below

    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    effective_log_level = LOG_LEVELS.get(log_level_name, logging.ERROR)

    # Get the root logger and remove any existing handlers.
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_log_level)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Also clear handlers from the qx logger to prevent any conflicts.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    logger.setLevel(effective_log_level)
    if log_file_path:
        # When QX_LOG_FILE is set, configure the root logger to write to a file.
        # This captures logs from all libraries (like litellm, httpx).
        log_file = Path(log_file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(file_handler)
        logger.propagate = True  # Ensure qx logs go to the root logger's file handler

        # Configure LiteLLM-specific loggers to also redirect to file only
        litellm_loggers = [
            "litellm",
            "litellm.proxy",
            "litellm.router",
            "litellm.utils",
            "litellm.llms",
            "LiteLLM",  # Some modules use this capitalization
        ]

        for logger_name in litellm_loggers:
            lib_logger = logging.getLogger(logger_name)
            lib_logger.setLevel(effective_log_level)
            # Remove any existing handlers from LiteLLM loggers
            for handler in lib_logger.handlers[:]:
                lib_logger.removeHandler(handler)
            # Ensure they propagate to root logger (which has file handler)
            lib_logger.propagate = True

    else:
        # When QX_LOG_FILE is not set, configure all loggers for console output.
        # This includes both qx and library logs.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(effective_log_level)
        console_handler.setFormatter(
            logging.Formatter("%(levelname)s - %(name)s: %(message)s")
        )
        root_logger.addHandler(console_handler)
        
        # Ensure qx logger uses root logger's handler
        logger.propagate = True

    # Enable debug logging for HTTP libraries if requested.
    # If QX_LOG_FILE is set, their logs will go to the file.
    # If not, they will be silenced by the handler-less root logger.
    if effective_log_level <= logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("openai").setLevel(logging.DEBUG)
        os.environ["HTTPX_LOG_LEVEL"] = "debug"

    # Set up global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )
        # Also write to file directly in case logger fails
        if log_file_path:
            with open(log_file_path, "a") as f:
                f.write("\n=== UNCAUGHT EXCEPTION ===\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
                f.write("=== END EXCEPTION ===\n\n")

    sys.excepthook = handle_exception

    logger.debug(
        f"Qx application log level set to: {logging.getLevelName(effective_log_level)} ({effective_log_level})"
    )
    if log_file_path:
        logger.debug(f"Logging to file: {log_file_path}")
    logger.debug("Global exception handler installed")


def remove_temp_stream_handler():
    global temp_stream_handler
    if temp_stream_handler and temp_stream_handler in logger.handlers:
        logger.removeHandler(temp_stream_handler)
        temp_stream_handler = None
