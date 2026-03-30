import logging
import structlog

# Structured logging configuration
logging.basicConfig(
    format='%(message)s',
    stream=sys.stdout,
    level=logging.INFO,
)

# Set up structlog to use the standard logging system
structlog.configure(
    processors=[
        structlog.processors.KeyValueRenderer(key_order=['event'])
    ],
)

logger = structlog.get_logger()