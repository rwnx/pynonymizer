from pynonymizer.database.basic.output import UnknownOutputTypeError, resolve_output, RawOutput, GzipOutput, StdOutOutput
from unittest.mock import mock_open, patch
import pytest

test_path_examples = [
    "",
    "complex/multi/part/path/test/",
    "complex\\multi\\part\\path\\test\\",
    "/absolute/path/test/",
    "C:\\absolute\\path\\test\\"
]


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_raw(path_example):
    test_path = path_example + "test.sql"
    assert isinstance(resolve_output(test_path), RawOutput)


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_gzip(path_example):
    test_path = path_example + "test.sql.gz"
    assert isinstance(resolve_output(test_path), GzipOutput)


def test_resolve_unknown():
    with pytest.raises(UnknownOutputTypeError):
        resolve_output("unknown_file.bbs")

def test_resolve_stdout():
    isinstance(resolve_output("-"), StdOutOutput)

def test_stdout_open():
    with patch("sys.stdout") as mock_stdout:
        std = StdOutOutput()

        assert std.open() is mock_stdout.buffer
