import logging
import os

import structlog

from doraemon.logger.slogger import configure_structlog


def test_configure_structlog_terminal_output(mock_terminal, caplog):
    configure_structlog(log_level=logging.INFO)
    logger = structlog.get_logger()

    with caplog.at_level(logging.INFO):
        logger.info("hello world", event_info="test event")

    assert any("test event" in message for message in caplog.messages)


def test_configure_structlog_json_output(mock_non_terminal, caplog):
    configure_structlog(log_level=logging.INFO)
    logger = structlog.get_logger()
    logger.info("hello world", event_info="test event")

    with caplog.at_level(logging.INFO):
        logger.info("hello world", event_info="test event")
        assert any(
            '{"event_info": "test event", "event": "hello world", "level": "info"}'
            in message
            for message in caplog.messages
        )


def test_configure_structlog_blacklist_replacement(mock_terminal, caplog):
    blacklist = [{"key": "password", "new_value": "***"}]
    configure_structlog(key_blacklist=blacklist)

    logger = structlog.get_logger()
    with caplog.at_level(logging.INFO):
        logger.info("sensitive log", password="123456", event_info="login")
        assert any("***" in message for message in caplog.messages)
        assert any("login" in message for message in caplog.messages)

    # Inner dict case
    with caplog.at_level(logging.INFO):
        logger.info(
            "sensitive log",
            login_info={"login_sensitive": {"password": "123456"}},
            event_info="login",
        )
        assert any("***" in message for message in caplog.messages)
        assert any("login" in message for message in caplog.messages)
        assert any("login_sensitive" in message for message in caplog.messages)


def test_configure_structlog_with_file_logging(temp_log_dir, mock_terminal):
    """测试配置文件日志并验证日志文件创建"""
    configure_structlog(log_level=logging.INFO, log_file_path=temp_log_dir)

    logger = structlog.get_logger()
    test_message = "test file logging with date suffix"
    logger.info(test_message, user_id=123, action="test")

    # 验证日志文件是否创建
    log_file = os.path.join(temp_log_dir, "local.log")
    assert os.path.exists(log_file), "Log file should be created"

    # 验证日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert test_message in content, "Log message should be in the file"


def test_log_file_handler_has_date_suffix(temp_log_dir):
    """测试日志文件 handler 配置了日期后缀"""
    configure_structlog(log_level=logging.INFO, log_file_path=temp_log_dir)

    # 获取 root logger 的 handlers
    root_logger = logging.getLogger()
    file_handlers = [h for h in root_logger.handlers if hasattr(h, "suffix")]

    # 验证至少有一个 file handler 配置了日期后缀
    assert len(file_handlers) > 0, "Should have at least one file handler"
    assert (
        file_handlers[0].suffix == "%Y-%m-%d"
    ), "File handler should have date suffix format"
    assert len(file_handlers) > 0, "Should have at least one file handler"
    assert (
        file_handlers[0].suffix == "%Y-%m-%d"
    ), "File handler should have date suffix format"
