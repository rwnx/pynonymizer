import unittest
from unittest.mock import Mock

from pynonymizer.fake import UnsupportedFakeTypeError
from pynonymizer.strategy import parser, database, table, update_column
from pynonymizer.strategy.exceptions import UnknownTableStrategyError, UnknownColumnStrategyError, ConfigSyntaxError
from pynonymizer.strategy.table import TableStrategyTypes
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes
import copy
import pytest


class ConfigParsingTests(unittest.TestCase):
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

    def setUp(self):
        self.fake_column_set = Mock()
        self.strategy_parser = parser.StrategyParser(self.fake_column_set)

    def test_valid_parse_no_mutate(self):
        old_valid_config = copy.deepcopy(self.valid_config)
        strategy = self.strategy_parser.parse_config(self.valid_config)

        assert self.valid_config == old_valid_config

    def test_valid_parse(self):
        strategy = self.strategy_parser.parse_config(self.valid_config)
        assert isinstance(strategy, database.DatabaseStrategy)

        assert strategy.table_strategies["accounts"].strategy_type == TableStrategyTypes.UPDATE_COLUMNS
        assert strategy.table_strategies["transactions"].strategy_type == TableStrategyTypes.TRUNCATE

        accounts_strategy = strategy.table_strategies["accounts"]
        assert accounts_strategy.column_strategies["current_sign_in_ip"].strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE

        assert accounts_strategy.column_strategies["username"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN
        assert accounts_strategy.column_strategies["email"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL
        assert accounts_strategy.column_strategies["name"].strategy_type == UpdateColumnStrategyTypes.EMPTY

    def test_unsupported_fake_column_type(self):
        """
        get_fake_column's UnsupportedFakeType should kill a parse attempt
        """
        self.fake_column_set.get_fake_column = Mock(side_effect=UnsupportedFakeTypeError("UNSUPPORTED_TYPE"))
        with pytest.raises(UnsupportedFakeTypeError):
            self.strategy_parser.parse_config(self.valid_config)

    def test_invalid_table_strategy_parse(self):
        with pytest.raises(UnknownTableStrategyError):
            self.strategy_parser.parse_config({
                "tables": {
                    "accounts": "cheesecake"
                }
            })

    def test_unknown_column_strategy(self):
        with pytest.raises(UnknownColumnStrategyError):
            self.strategy_parser.parse_config({
                "tables": {
                    "accounts": {
                        "columns": {
                            "current_sign_in_ip": {
                                "type": "cheese"  # Not a valid strategy
                            }
                        }
                    },

                    "transactions": "truncate"
                }
            })

    def test_unknown_table_strategy_bad_dict(self):
        with pytest.raises(UnknownTableStrategyError):
            self.strategy_parser.parse_config({
                "tables": {
                    "accounts": {
                        "not_columns": {
                            "current_sign_in_ip": "ipv4_public",
                            "username": "unique_login",
                            "email": "unique_email",
                            "name": "empty",
                        }
                    },
                }
            })

    def test_valid_parse_before_after_script(self):
        parse_result = self.strategy_parser.parse_config({
            "scripts": {
                "before": [
                    "SELECT `before` from `students`;"
                ],
                "after": [
                    "SELECT `after` from `students`;",
                    "SELECT `after_2` from `example`;"
                ]
            },
            "tables": {
                "accounts": "truncate"
            },
        })

        assert isinstance(parse_result, database.DatabaseStrategy)

        assert len(parse_result.table_strategies) == 1
        assert parse_result.table_strategies["accounts"].strategy_type == TableStrategyTypes.TRUNCATE

        assert parse_result.scripts["before"] == [
                    "SELECT `before` from `students`;"
                ]
        assert parse_result.scripts["after"] == [
                    "SELECT `after` from `students`;",
                    "SELECT `after_2` from `example`;"
                ]

    def test_verbose_table_truncate(self):
        strategy = self.strategy_parser.parse_config({
            "tables": {
                "table1": {
                    "type": "truncate",
                    # parser should ignore keys from other types when type is specified
                    "columns": {}
                }
            }
        })

        assert strategy.table_strategies["table1"].strategy_type == TableStrategyTypes.TRUNCATE

    def test_verbose_table_update_columns(self):
        strategy = self.strategy_parser.parse_config({
            "tables": {
                "table1": {
                    "type": "update_columns",
                    "columns": {
                    }
                }
            }
        })

        assert strategy.table_strategies["table1"].strategy_type == TableStrategyTypes.UPDATE_COLUMNS

    def test_table_raises_when_given_unrelated_key(self):
        with pytest.raises(ConfigSyntaxError):
            strategy = self.strategy_parser.parse_config({
                "tables": {
                    "table1": {
                        "type": "update_columns",
                        "columns": {
                            "column1": {
                                "type": "empty",
                                "where": "condition = 'value1'",
                                "fake_type": "email"
                            },
                        }
                    }
                }
            })

    def test_verbose_table_update_columns_verbose(self):
        strategy = self.strategy_parser.parse_config({
            "tables": {
                "table1": {
                    "type": "update_columns",
                    "columns": {
                        "column1": {
                            "type": "empty",
                            "where": "condition = 'value1'",
                        },
                        "column2": {
                            "type": "fake_update",
                            "fake_type": "email",
                        },
                        "column3": {
                            "type": "unique_login",
                        },
                        "column4": {
                            "type": "unique_email",
                        },
                        "column5": {
                            "type": "literal",
                            "value": "RAND()"
                        }
                    }
                }
            }
        })

        assert strategy.table_strategies["table1"].strategy_type == TableStrategyTypes.UPDATE_COLUMNS

        assert strategy.table_strategies["table1"].column_strategies["column1"].strategy_type == UpdateColumnStrategyTypes.EMPTY
        assert strategy.table_strategies["table1"].column_strategies["column2"].strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE
        assert strategy.table_strategies["table1"].column_strategies["column2"].fake_type == "email"
        assert strategy.table_strategies["table1"].column_strategies["column3"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN
        assert strategy.table_strategies["table1"].column_strategies["column4"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL
        assert strategy.table_strategies["table1"].column_strategies["column5"].strategy_type == UpdateColumnStrategyTypes.LITERAL
        assert strategy.table_strategies["table1"].column_strategies["column5"].value == "RAND()"

    def test_verbose_table_all_update_columns_where(self):
        strategy = self.strategy_parser.parse_config({
            "tables": {
                "table1": {
                    "type": "update_columns",
                    "columns": {
                        "column1": {
                            "type": "empty",
                            "where": "condition = 'value1'"
                        },
                        "column2": {
                            "type": "fake_update",
                            "fake_type": "email",
                            "where": "condition = 'value2'"
                        },
                        "column3": {
                            "type": "unique_login",
                            "where": "condition = 'value3'"
                        },
                        "column4": {
                            "type": "unique_email",
                            "where": "condition = 'value4'"
                        },
                    }
                }
            }
        })

        assert strategy.table_strategies["table1"].strategy_type == TableStrategyTypes.UPDATE_COLUMNS

        assert strategy.table_strategies["table1"].column_strategies["column1"].strategy_type == UpdateColumnStrategyTypes.EMPTY
        assert strategy.table_strategies["table1"].column_strategies["column1"].where_condition == "condition = 'value1'"

        assert strategy.table_strategies["table1"].column_strategies["column2"].strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE
        assert strategy.table_strategies["table1"].column_strategies["column2"].where_condition == "condition = 'value2'"

        assert strategy.table_strategies["table1"].column_strategies["column3"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN
        assert strategy.table_strategies["table1"].column_strategies["column3"].where_condition == "condition = 'value3'"

        assert strategy.table_strategies["table1"].column_strategies["column4"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL
        assert strategy.table_strategies["table1"].column_strategies["column4"].where_condition == "condition = 'value4'"



