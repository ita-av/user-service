import logging
import os
import sys

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logger(name: str = "barbershop-user-service"):
    """Set up and return a logger with the specified name."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    logger.propagate = False

    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    return logger


# Create the main logger
logger = setup_logger()


def get_logger(name: str = None):
    """Get a child logger of the main logger."""
    if name:
        return setup_logger(f"barbershop-user-service.{name}")
    return logger
