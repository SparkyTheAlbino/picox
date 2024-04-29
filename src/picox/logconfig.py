import logging
import sys

formatter = logging.Formatter('%(levelname)s: %(message)s')

LOGGER = logging.getLogger(__name__)

LOGGER.setLevel(logging.DEBUG)

# Create handlers for different streams
stdout_handler = logging.StreamHandler(sys.stdout)
stderr_handler = logging.StreamHandler(sys.stderr)

stdout_handler.addFilter(lambda record: record.levelno <= logging.WARNING)  # DEBUG, INFO, WARNING
stderr_handler.addFilter(lambda record: record.levelno >= logging.ERROR)    # ERROR, CRITICAL

stdout_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)

LOGGER.addHandler(stdout_handler)
LOGGER.addHandler(stderr_handler)