import unittest
import pynonymizer.input


class ResolveInput(unittest.TestCase):
    test_path_examples = [
        "",
        "complex/multi/part/path/test/",
        "complex\\multi\\part\\path\\test\\",
        "/absolute/path/test/",
        "C:\\absolute\\path\\test\\"
    ]

    def test_resolve_raw_input(self):
        for path in self.test_path_examples:
            test_path = path + "test.sql"
            with self.subTest(i=test_path):
                self.assertIsInstance(pynonymizer.input.get_input(test_path), pynonymizer.input.RawInput)

    def test_resolve_gzip_input(self):
        for path in self.test_path_examples:
            test_path = path + "test.sql.gz"
            with self.subTest(i=test_path):
                self.assertIsInstance(pynonymizer.input.get_input(test_path), pynonymizer.input.GzipInput)