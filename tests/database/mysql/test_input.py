import pytest
from unittest import TestCase
from unittest.mock import mock_open, patch
from pynonymizer.database.basic.input import GzipInput, RawInput, UnknownInputTypeError, resolve_input


def test_gzip_open():
    with patch("gzip.open", mock_open(read_data=b"data")) as mock_file:
        gz = GzipInput("testfile.gz")
        open_result = gz.open()

        mock_file.assert_called_with("testfile.gz", "rb")
        assert open_result == mock_file.return_value


def test_gzip_get_size():
    with patch("builtins.open", mock_open(read_data=b'X\x1f\x00\x00')) as mock_file:
        gz = GzipInput("testfile.gz")
        assert gz.get_size() == 8024


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


class ResolveFromFilepathTest(TestCase):
    test_path_examples = [
        "",
        "complex/multi/part/path/test/",
        "complex\\multi\\part\\path\\test\\",
        "/absolute/path/test/",
        "C:\\absolute\\path\\test\\"
    ]

    def test_resolve_raw(self):
        for path in self.test_path_examples:
            test_path = path + "test.sql"
            with self.subTest(i=test_path):
                assert isinstance(resolve_input(test_path), RawInput)

    def test_resolve_gzip(self):
        for path in self.test_path_examples:
            test_path = path + "test.sql.gz"
            with self.subTest(i=test_path):
                assert isinstance(resolve_input(test_path), GzipInput)

    def test_resolve_unknown(self):
        with pytest.raises(UnknownInputTypeError):
            resolve_input("unknown_file.bbs")