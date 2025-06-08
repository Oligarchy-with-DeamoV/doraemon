import os

import structlog

from doraemon.logger.slogger import configure_structlog

## ==> FORCE_JSON_LOGGING
## command: FORCE_JSON_LOGGING=INFO poetry run python3 logger_example.py

## ==> File save
configure_structlog(log_file_path="./")
logger = structlog.getLogger(__name__)
logger.info("hi")
logger.debug("fuck")
logger.error("oh no")


## ==> black list filtering
sc = {"sealedKey": "shamed"}
configure_structlog(key_blacklist=[{"key": "sealedKey", "new_value": "xxxxxxx"}])
logger = structlog.getLogger(__name__)
logger.info("hi", sealedKey="secretContent")
logger.info("hi", sealedObject=sc)
logger.debug("fuck")
logger.error("oh no")
