import unittest
from unittest.mock import patch

from pynonymizer.log import get_logger, get_default_logger


@patch("logging.getLogger")
class TestLogMethods(unittest.TestCase):
    def test_get_default_logger(self, getLoggerMock):
        logger = get_default_logger()
        getLoggerMock.assert_called_once_with("pynonymizer")

    def test_simple_name(self, getLoggerMock):
        logger = get_logger("test")
        getLoggerMock.assert_called_once_with("pynonymizer.test")

    def test_multipart_name(self, getLoggerMock):
        logger = get_logger(["a", "b", "cd", "ef", "ghi"])
        getLoggerMock.assert_called_once_with("pynonymizer.a.b.cd.ef.ghi")

