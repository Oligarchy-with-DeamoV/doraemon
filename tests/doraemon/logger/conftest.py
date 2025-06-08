import os
import pytest
import tempfile
from unittest import mock


@pytest.fixture
def temp_log_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def mock_terminal():
    with mock.patch("sys.stderr.isatty", return_value=True):
        yield


@pytest.fixture
def mock_non_terminal():
    with mock.patch("sys.stderr.isatty", return_value=False):
        yield


@pytest.fixture
def mock_file_handler():
    with mock.patch("doraemon.logger.file_handler.get_file_handler") as mock_handler:
        yield mock_handler
