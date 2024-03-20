from pynonymizer.database.input import (
    GzipInput,
    RawInput,
    StdInInput,
    UnknownInputTypeError,
    resolve_input,
)
from pynonymizer.database.output import (
    UnknownOutputTypeError,
    resolve_output,
    RawOutput,
    GzipOutput,
    StdOutOutput,
    XzOutput,
)
import pytest

test_path_examples = [
    "",
    "complex/multi/part/path/test/",
    "complex\\multi\\part\\path\\test\\",
    "/absolute/path/test/",
    "C:\\absolute\\path\\test\\",
]


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_raw(path_example):
    test_path = path_example + "test.sql"
    assert isinstance(resolve_output(test_path), RawOutput)


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_gzip(path_example):
    test_path = path_example + "test.sql.gz"
    assert isinstance(resolve_output(test_path), GzipOutput)


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_xz(path_example):
    test_path = path_example + "test.sql.xz"
    assert isinstance(resolve_output(test_path), XzOutput)


def test_resolve_unknown():
    with pytest.raises(UnknownOutputTypeError):
        resolve_output("unknown_file.bbs")


def test_resolve_stdout():
    isinstance(resolve_output("-"), StdOutOutput)


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_raw(path_example):
    test_path = path_example + "test.sql"
    assert isinstance(resolve_input(test_path), RawInput)


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_gzip(path_example):
    test_path = path_example + "test.sql.gz"
    assert isinstance(resolve_input(test_path), GzipInput)


def test_resolve_unknown():
    with pytest.raises(UnknownInputTypeError):
        resolve_input("unknown_file.bbs")


def test_resolve_stdout():
    isinstance(resolve_input("-"), StdInInput)
