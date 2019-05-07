import pynonymizer.output
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
    assert isinstance(pynonymizer.output.from_location(test_path), pynonymizer.output.RawOutput)


@pytest.mark.parametrize("path_example", test_path_examples)
def test_resolve_gzip(path_example):
    test_path = path_example + "test.sql.gz"
    assert isinstance(pynonymizer.output.from_location(test_path), pynonymizer.output.GzipOutput)
