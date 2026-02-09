import logging
import os
import tempfile

from doraemon.logger.file_handler import get_file_handler


def test_file_handler_has_date_suffix():
    """测试 file handler 是否配置了日期后缀"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "test.log")
        handler = get_file_handler(
            log_level=logging.INFO,
            file_name=log_file,
            rotation_when="midnight",
            rotation_interval=1,
            backup_count=30,
        )

        # 验证 handler 设置了正确的日期后缀格式
        assert handler.suffix == "%Y-%m-%d", "Handler should have date suffix format"

        handler.close()


def test_file_handler_creates_log_file():
    """测试 file handler 能够创建日志文件"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "test.log")
        handler = get_file_handler(
            log_level=logging.INFO,
            file_name=log_file,
        )

        # 创建 logger 并写入日志
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        logger.info("Test log message")
        handler.flush()

        # 验证日志文件存在
        assert os.path.exists(log_file), "Log file should be created"

        # 验证日志文件内容
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Test log message" in content, "Log message should be in the file"

        handler.close()


def test_file_handler_rotation_settings():
    """测试 file handler 的轮转设置"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "test.log")
        handler = get_file_handler(
            log_level=logging.DEBUG,
            file_name=log_file,
            rotation_when="midnight",
            rotation_interval=1,
            backup_count=10,
        )

        # 验证轮转设置
        assert handler.when == "MIDNIGHT", "Handler should rotate at midnight"
        assert handler.backupCount == 10, "Handler should keep 10 backup files"
        assert handler.suffix == "%Y-%m-%d", "Handler should have date suffix"

        handler.close()


def test_file_handler_encoding():
    """测试 file handler 使用 UTF-8 编码"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "test.log")
        handler = get_file_handler(
            log_level=logging.INFO,
            file_name=log_file,
        )

        # 创建 logger 并写入包含中文的日志
        logger = logging.getLogger("test_utf8_logger")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        chinese_message = "测试中文日志消息"
        logger.info(chinese_message)
        handler.flush()

        # 验证可以正确读取中文内容
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert (
                chinese_message in content
            ), "Chinese characters should be correctly encoded"

        handler.close()


def test_file_handler_log_level():
    """测试 file handler 的日志级别过滤"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "test.log")
        handler = get_file_handler(
            log_level=logging.WARNING,  # 只记录 WARNING 及以上级别
            file_name=log_file,
        )

        logger = logging.getLogger("test_level_logger")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # 写入不同级别的日志
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        handler.flush()

        # 读取日志文件内容
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            # 由于 handler 级别是 WARNING，只有 WARNING 和 ERROR 应该被记录
            assert "Debug message" not in content
            assert "Info message" not in content
            assert "Warning message" in content
            assert "Error message" in content

        handler.close()
        handler.close()
