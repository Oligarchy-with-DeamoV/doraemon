import logging
from logging.handlers import TimedRotatingFileHandler


def get_file_handler(
    log_level: int,
    file_name: str,
    rotation_when="midnight",
    rotation_interval=1,
    backup_count=30,
):
    handler = TimedRotatingFileHandler(
        file_name,
        when=rotation_when,
        interval=rotation_interval,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    return handler
