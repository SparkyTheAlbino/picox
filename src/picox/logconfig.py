import logging
import sys

def get_package_logger():
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