import unittest
from unittest.mock import Mock

from pynonymizer.fake import UnsupportedFakeTypeError
from pynonymizer.strategy import database
from pynonymizer.strategy.exceptions import UnknownTableStrategyError, UnknownColumnStrategyError, ConfigSyntaxError
from pynonymizer.strategy.table import TableStrategyTypes
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes
import copy
import pytest


@pytest.fixture
def simple_config():
    return {
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

@pytest.fixture
def config_unsupported_fake_type():
    return {
            "tables": {
                "accounts": {
                    "columns": {
                        "current_sign_in_ip": "ipv4_public",
                        "username": "unique_login",
                        "email": "NOT A VALID FAKE TYPE",
                        "name": "empty",
                    }
                },

                "transactions": "truncate"
            }
        }

@pytest.fixture
def fake_column_generator():
    from pynonymizer.fake import FakeColumnGenerator
    return FakeColumnGenerator()


@pytest.fixture
def strategy_parser(fake_column_generator):
    from pynonymizer.strategy import parser
    return parser.StrategyParser(fake_column_generator)


def test_valid_parse_no_mutate(simple_config, strategy_parser):
    old_valid_config = copy.deepcopy(simple_config)
    strategy_parser.parse_config(simple_config)

    assert simple_config == old_valid_config


def test_valid_parse(simple_config, strategy_parser):
    strategy = strategy_parser.parse_config(simple_config)
    assert isinstance(strategy, database.DatabaseStrategy)

    assert strategy.table_strategies["accounts"].strategy_type == TableStrategyTypes.UPDATE_COLUMNS
    assert strategy.table_strategies["transactions"].strategy_type == TableStrategyTypes.TRUNCATE

    accounts_strategy = strategy.table_strategies["accounts"]
    assert accounts_strategy.column_strategies["current_sign_in_ip"].strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE

    assert accounts_strategy.column_strategies["username"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN
    assert accounts_strategy.column_strategies["email"].strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL
    assert accounts_strategy.column_strategies["name"].strategy_type == UpdateColumnStrategyTypes.EMPTY


def test_unsupported_fake_column_type(strategy_parser, config_unsupported_fake_type):
    """
    get_fake_column's UnsupportedFakeType should kill a parse attempt
    """

    with pytest.raises(UnsupportedFakeTypeError):
        strategy_parser.parse_config(config_unsupported_fake_type)


def test_invalid_table_strategy_parse(strategy_parser):
    with pytest.raises(UnknownTableStrategyError):
        strategy_parser.parse_config({
            "tables": {
                "accounts": "cheesecake"
            }
        })


def test_unknown_column_strategy(strategy_parser):
    with pytest.raises(UnknownColumnStrategyError):
        strategy_parser.parse_config({
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


def test_unknown_table_strategy_bad_dict(strategy_parser):
    with pytest.raises(UnknownTableStrategyError):
        strategy_parser.parse_config({
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


def test_valid_parse_before_after_script(strategy_parser):
    parse_result = strategy_parser.parse_config({
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


def test_verbose_table_truncate(strategy_parser):
    strategy = strategy_parser.parse_config({
        "tables": {
            "table1": {
                "type": "truncate",
                # parser should ignore keys from other types when type is specified
                "columns": {}
            }
        }
    })

    assert strategy.table_strategies["table1"].strategy_type == TableStrategyTypes.TRUNCATE


def test_verbose_table_update_columns(strategy_parser):
    strategy = strategy_parser.parse_config({
        "tables": {
            "table1": {
                "type": "update_columns",
                "columns": {
                }
            }
        }
    })

    assert strategy.table_strategies["table1"].strategy_type == TableStrategyTypes.UPDATE_COLUMNS


def test_table_raises_when_given_unrelated_key(strategy_parser):
    with pytest.raises(ConfigSyntaxError):
        strategy_parser.parse_config({
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


def test_verbose_table_update_columns_verbose(strategy_parser):
    strategy = strategy_parser.parse_config({
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


def test_verbose_table_all_update_columns_where(strategy_parser):
    strategy = strategy_parser.parse_config({
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



