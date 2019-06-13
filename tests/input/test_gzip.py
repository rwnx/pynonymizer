import pytest
from unittest.mock import mock_open, patch

from pynonymizer.input.gzip import GzipInput

def test_gzip_open():
    with patch("gzip.open", mock_open(read_data=b"data")) as mock_file:
        gz = GzipInput("testfile.gz")
        open_result = gz.open()

        mock_file.assert_called_with("testfile.gz")
        assert open_result == mock_file.return_value

def test_gzip_get_size():
    with patch("builtins.open", mock_open(read_data=b'X\x1f\x00\x00')) as mock_file:
        gz = GzipInput("testfile.gz")
        assert gz.get_size() == 8024