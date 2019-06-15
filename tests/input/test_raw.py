import pytest
from unittest.mock import mock_open, patch

from pynonymizer.input.raw import RawInput


def test_raw_open():
    """
    rawfile should return the file object directly
    """
    with patch("builtins.open", mock_open(read_data=b"data")) as mock_file:
        raw = RawInput("testfile.sql")
        open_result = raw.open()

        assert open_result == mock_file.return_value


@patch("os.path.getsize", autospec=True)
def test_raw_get_size(getsize):
    """
    rawfile should use os.path.getsize to bring back a size
    """
    raw = RawInput("testfile.sql")

    size_result = raw.get_size()
    assert size_result == getsize.return_value