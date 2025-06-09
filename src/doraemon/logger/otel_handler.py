import logging

import opentelemetry._logs as logs
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource


def create_otel_log_handler(service_name: str, otel_collector_endpoint: str):
    resource = Resource.create({SERVICE_NAME: service_name})
    logs.set_logger_provider(LoggerProvider(resource=resource))
    logger_provider = logs.get_logger_provider()
    otlp_log_exporter = OTLPLogExporter(endpoint=otel_collector_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    return otel_handler
