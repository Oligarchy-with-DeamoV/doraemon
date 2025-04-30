import os
from doraemon.logger.slogger import configure_structlog
import structlog

os.environ["FORCE_JSON_LOGGING"] = "INFO"

configure_structlog()
logger = structlog.getLogger(__name__)

logger.info("hi")
logger.debug("fuck")
logger.error("oh no")
