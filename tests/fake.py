import unittest
from unittest.mock import Mock

import pynonymizer.fake


class TestFakeColumn(unittest.TestCase):
    def setUp(self):
        self.faker = Mock()
        self.faker.test_field = Mock()

        self.implicit_generator_args = (self.faker, "test_field", "VARCHAR(10)")
        self.explicit_generator_args = (self.faker, "test_field", "VARCHAR(10)", lambda: "value")

    def test_fields(self):
        fake_column = pynonymizer.fake.FakeColumn(*self.implicit_generator_args)

        self.assertEqual(fake_column.name, "test_field")
        self.assertEqual(fake_column.sql_type, "VARCHAR(10)")

    def test_implicit_generator(self):
        fake_column = pynonymizer.fake.FakeColumn(*self.implicit_generator_args)

        # implicit generator should call faker method by the same name when asked for a value
        fake_value = fake_column.get_value()
        self.faker.test_field.assert_called()

    def test_explicit_generator(self):
        fake_column = pynonymizer.fake.FakeColumn(*self.explicit_generator_args)

        # explicit generator should NOT call faker, as the explicit generator should take precedence
        fake_value = fake_column.get_value()
        self.faker.test_field.assert_not_called()
        self.assertEqual(fake_value, "value")



