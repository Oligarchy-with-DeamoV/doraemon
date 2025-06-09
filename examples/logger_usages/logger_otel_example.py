import logging
import os

import structlog

from doraemon.logger.slogger import configure_structlog

# FORCE_JSON_LOGGING=INFO poetry run python3 logger_otel_example.py
# sudo docker compose -f least_middleware_deployment.yaml up
# 登入 kafka-client docker exec -it kafka-client bash
# 查看 topic：kafka-topics --bootstrap-server kafka:9092 --list
# 查看日志：kafka-console-consumer --bootstrap-server kafka:9092 --topic otel-logs --from-beginning

## ==> opentelemery
otel_config = {
    "service_name": "test123",
    "otel_collector_endpoint": "http://0.0.0.0:4317",
}
sc = {"sealedKey": "shamed"}
configure_structlog(otel_config=otel_config)
logger = structlog.getLogger(__name__)
logger.info("hi", sealedKey="secretContent")
logger.info("hi", sealedObject=sc)
logger.debug("fuck")
logger.error("oh no")
