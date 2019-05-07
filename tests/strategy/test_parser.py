import unittest
from unittest.mock import Mock

from pynonymizer.fake import UnsupportedFakeTypeError
from pynonymizer.strategy import parser, database, table, update_column
from pynonymizer.strategy.exceptions import UnknownTableStrategyError
import pytest

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

class ConfigParsingTest(unittest.TestCase):
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
        self.fake_column_set = Mock()
        self.strategy_parser = parser.StrategyParser(self.fake_column_set)

    def test_valid_parse(self):
        strategy = self.strategy_parser.parse_config(self.valid_config)
        assert isinstance(strategy, database.DatabaseStrategy)

        assert isinstance(strategy.table_strategies["accounts"], table.UpdateColumnsTableStrategy)
        assert isinstance(strategy.table_strategies["transactions"], table.TruncateTableStrategy)

        accounts_strategy = strategy.table_strategies["accounts"]
        assert isinstance(accounts_strategy.column_strategies["current_sign_in_ip"], update_column.FakeUpdateColumnStrategy)
        self.fake_column_set.get_fake_column.assert_called_once_with("ipv4_public")

        assert isinstance(accounts_strategy.column_strategies["username"], update_column.UniqueLoginUpdateColumnStrategy)
        assert isinstance(accounts_strategy.column_strategies["email"], update_column.UniqueEmailUpdateColumnStrategy)
        assert isinstance(accounts_strategy.column_strategies["name"], update_column.EmptyUpdateColumnStrategy)

    def test_unsupported_fake_column_type(self):
        """
        get_fake_column's UnsupportedFakeType should kill a parse attempt
        """
        self.fake_column_set.get_fake_column = Mock(side_effect=UnsupportedFakeTypeError("test"))
        with pytest.raises(UnsupportedFakeTypeError):
            self.strategy_parser.parse_config(self.valid_config)

    def test_invalid_table_strategy_parse(self):
        with pytest.raises(UnknownTableStrategyError):
            self.strategy_parser.parse_config(self.invalid_table_strategy_config)

