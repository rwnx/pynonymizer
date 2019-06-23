import unittest
import pynonymizer.input
import pytest
from pynonymizer.input import UnknownInputTypeError


class ResolveFromFilepathTest(unittest.TestCase):
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
                assert isinstance(pynonymizer.input.from_location(test_path), pynonymizer.input.RawInput)

    def test_resolve_gzip(self):
        for path in self.test_path_examples:
            test_path = path + "test.sql.gz"
            with self.subTest(i=test_path):
                assert isinstance(pynonymizer.input.from_location(test_path), pynonymizer.input.GzipInput)

    def test_resolve_unknown(self):
        with pytest.raises(UnknownInputTypeError):
            pynonymizer.input.from_location("unknown_file.bbs")