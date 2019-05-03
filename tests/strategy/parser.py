import unittest
from unittest.mock import Mock

from pynonymizer.strategy import parser, database, table, update_column
from pynonymizer.strategy.exceptions import UnknownTableStrategyError
from pynonymizer.strategy.update_column import UnsupportedFakeTypeError

"""
tables:
  accounts:
    columns:
      current_sign_in_ip: ipv4_public
      last_sign_in_ip: ipv4_public
      username: user_name
      email: company_email
  transactions: truncate
  other_important_table: truncate
"""


class ConfigParsing(unittest.TestCase):
    valid_config = {
        "tables": {
            "accounts": {
                "columns": {
                    "current_sign_in_ip": "ipv4_public",
                    "username": "unique_login",
                    "email": "unique_email",
                    "name": "empty",
                }
            },

            "transactions": "truncate"
        }
    }

    invalid_table_strategy_config = {
        "tables": {
            "accounts": "cheesecake"
        }
    }

    def setUp(self):
        self.fake_seeder = Mock()
        self.strategy_parser = parser.StrategyParser(self.fake_seeder)

    def test_valid_parse(self):
        strategy = self.strategy_parser.parse_config(self.valid_config)
        self.assertIsInstance(strategy, database.DatabaseStrategy)

        self.assertIsInstance(strategy.table_strategies["accounts"], table.UpdateColumnsTableStrategy)
        self.assertIsInstance(strategy.table_strategies["transactions"], table.TruncateTableStrategy)

        accounts_strategy = strategy.table_strategies["accounts"]
        self.assertIsInstance(accounts_strategy.column_strategies["current_sign_in_ip"], update_column.FakeUpdateColumnStrategy)
        self.assertIsInstance(accounts_strategy.column_strategies["username"], update_column.UniqueLoginUpdateColumnStrategy)
        self.assertIsInstance(accounts_strategy.column_strategies["email"], update_column.UniqueEmailUpdateColumnStrategy)
        self.assertIsInstance(accounts_strategy.column_strategies["name"], update_column.EmptyUpdateColumnStrategy)

    def test_unsupported_fake_column_type(self):
        self.fake_seeder.supports_fake_type = Mock(return_value=False)
        with self.assertRaises(UnsupportedFakeTypeError):
            self.strategy_parser.parse_config(self.valid_config)

    def test_invalid_table_strategy_parse(self):
        with self.assertRaises(UnknownTableStrategyError):
            self.strategy_parser.parse_config(self.invalid_table_strategy_config)

