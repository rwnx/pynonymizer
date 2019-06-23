import unittest
from unittest.mock import Mock, patch
import pytest

from pynonymizer.fake import FakeColumnGenerator, FakeDataType, UnsupportedFakeTypeError
from faker import Faker


class FakeColumnGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.generator = FakeColumnGenerator()

    def test_supports_supported(self):
        assert self.generator.supports("first_name") is True

    def test_supports_unsupported_method(self):
        assert self.generator.supports("NOT A VALID METHOD") is False

    def test_supports_unsupported_args(self):
        assert self.generator.supports("first_name", {"arg1": 2, "arg2": 3}) is False

    def test_get_data_type_known_column(self):
        assert self.generator.get_data_type("date") == FakeDataType.DATE

    def test_get_data_type_unknown_column(self):
        assert self.generator.get_data_type("user_agent") == FakeDataType.STRING

    @patch("pynonymizer.fake.Faker")
    def test_get_value_supported(self, faker):
        faker.return_value = Mock(spec=Faker())
        faked_generator = FakeColumnGenerator()
        assert faked_generator.get_value("first_name") == faker().first_name()

    @patch("pynonymizer.fake.Faker")
    def test_get_value_unsupported(self, faker):
        faker.return_value = Mock(spec=Faker())
        faked_generator = FakeColumnGenerator()
        with pytest.raises(UnsupportedFakeTypeError):
            faked_generator.get_value("NOT A VALID METHOD")

    @patch("pynonymizer.fake.Faker")
    def test_get_value_unsupported_args(self, faker):
        faker.return_value = Mock(spec=Faker())
        faked_generator = FakeColumnGenerator()
        with pytest.raises(UnsupportedFakeTypeError):
            faked_generator.get_value("ean", {"not_valid_length": 13})