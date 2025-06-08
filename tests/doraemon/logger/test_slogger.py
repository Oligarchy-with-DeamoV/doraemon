import os
import logging
import structlog
from doraemon.logger.slogger import configure_structlog


def test_configure_structlog_terminal_output(mock_terminal, caplog):
    configure_structlog(log_level=logging.INFO)
    logger = structlog.get_logger()

    with caplog.at_level(logging.INFO):
        logger.info("hello world", event_info="test event")

    assert any('test event' in message for message in caplog.messages)


def test_configure_structlog_json_output(mock_non_terminal, caplog):
    configure_structlog(log_level=logging.INFO)
    logger = structlog.get_logger()
    logger.info("hello world", event_info="test event")

    with caplog.at_level(logging.INFO):
        logger.info("hello world", event_info="test event")
        assert any('{"event_info": "test event", "event": "hello world", "level": "info"}' in message for message in caplog.messages)


def test_configure_structlog_blacklist_replacement(mock_terminal, caplog):
    blacklist = [{"key": "password", "new_value": "***"}]
    configure_structlog(key_blacklist=blacklist)

    logger = structlog.get_logger()
    with caplog.at_level(logging.INFO):
        logger.info("sensitive log", password="123456", event_info="login")
        assert any('***' in message for message in caplog.messages)
        assert any('login' in message for message in caplog.messages)

    # Inner dict case
    with caplog.at_level(logging.INFO):
        logger.info("sensitive log", login_info={"login_sensitive": {'password': "123456"}}, event_info="login")
        assert any('***' in message for message in caplog.messages)
        assert any('login' in message for message in caplog.messages)
        assert any('login_sensitive' in message for message in caplog.messages)
