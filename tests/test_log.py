from unittest.mock import patch
import pytest
from pynonymizer.log import get_logger, get_default_logger


@patch("logging.getLogger")
def test_get_default_logger(get_logger_mock):
    logger = get_default_logger()
    get_logger_mock.assert_called_once_with("pynonymizer")


@patch("logging.getLogger")
def test_simple_name(get_logger_mock):
    logger = get_logger("test")
    get_logger_mock.assert_called_once_with("pynonymizer.test")


@patch("logging.getLogger")
def test_multipart_name(get_logger_mock):
    logger = get_logger(["a", "b", "cd", "ef", "ghi"])
    get_logger_mock.assert_called_once_with("pynonymizer.a.b.cd.ef.ghi")


@patch("logging.getLogger")
def test_no_logger_name_array(get_logger_mock):
    with pytest.raises(ValueError):
        logger = get_logger([])


@patch("logging.getLogger")
def test_no_logger_name_str(get_logger_mock):
    with pytest.raises(ValueError):
        logger = get_logger("")