import logging
import sys

def setup_logger() -> logging.Logger:
    """
    Configure a Logger in the style of this package
    Two stream handlers are defined to split stderr and stdout
    returns:
        logging.Logger
    """
    formatter = logging.Formatter('%(levelname)s: %(message)s')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create handlers for different streams
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)

    # Correctly filter log levels to ensure correct stream is used
    stdout_handler.addFilter(lambda record: record.levelno <= logging.WARNING)  # DEBUG, INFO, WARNING
    stderr_handler.addFilter(lambda record: record.levelno >= logging.ERROR)    # ERROR, CRITICAL

    # Apply formatters for both streams
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    return logger


LOGGER = setup_logger()