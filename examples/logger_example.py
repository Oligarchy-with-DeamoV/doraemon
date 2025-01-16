import os
from doraemon.logger.slogger import create_logger, configure_structlog

os.environ["FORCE_JSON_LOGGING"] = "INFO"

configure_structlog()
logger = create_logger(__name__)

logger.info("hi")
logger.debug("fuck")
logger.error("oh no")
