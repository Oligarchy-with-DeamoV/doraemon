import logging
from logging.handlers import RotatingFileHandler


def get_file_handler(log_level: int, file_name: str):
    handler = RotatingFileHandler(file_name, maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    return handler
