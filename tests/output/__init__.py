import unittest
import pynonymizer.output


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
                self.assertIsInstance(pynonymizer.output.from_location(test_path), pynonymizer.output.RawOutput)

    def test_resolve_gzip(self):
        for path in self.test_path_examples:
            test_path = path + "test.sql.gz"
            with self.subTest(i=test_path):
                self.assertIsInstance(pynonymizer.output.from_location(test_path), pynonymizer.output.GzipOutput)