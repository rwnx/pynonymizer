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

    accounts_strategy = strategy.table_strategies[0]
    transactions_strategy = strategy.table_strategies[1]

    assert accounts_strategy.table_name == "accounts"
    assert transactions_strategy.table_name == "transactions"

    assert accounts_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS
    assert transactions_strategy.strategy_type == TableStrategyTypes.TRUNCATE

    # need a better matching technique than checking list indicies.
    """
    assert accounts_strategy.column_strategies[0].strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE

    assert accounts_strategy.column_strategies[1].strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN
    assert accounts_strategy.column_strategies[2].strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL
    assert accounts_strategy.column_strategies[3].strategy_type == UpdateColumnStrategyTypes.EMPTY
    """



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
    assert parse_result.table_strategies[0].strategy_type == TableStrategyTypes.TRUNCATE

    assert parse_result.scripts["before"] == [
                "SELECT `before` from `students`;"
            ]
    assert parse_result.scripts["after"] == [
                "SELECT `after` from `students`;",
                "SELECT `after_2` from `example`;"
            ]


def test_verbose_table_truncate(strategy_parser):
    with pytest.raises(ConfigSyntaxError):
        strategy = strategy_parser.parse_config({
            "tables": {
                "table1": {
                    "type": "truncate",
                    # parser should raise error when keys from other types when type is specified
                    "columns": {}
                }
            }
        })


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

    assert len(strategy.table_strategies) == 1
    assert strategy.table_strategies[0].table_name == "table1"
    assert strategy.table_strategies[0].strategy_type == TableStrategyTypes.UPDATE_COLUMNS


def test_verbose_table_list_duplicate(strategy_parser):
    """parser should allow multiple tables of the same name in list-parse-mode"""
    strategy = strategy_parser.parse_config({
        "tables": [
            {
                "table_name": "table1",
                "type": "truncate",
            },
            {
                "table_name": "table1",
                "type": "truncate",
            }
        ]
    })

    assert len(strategy.table_strategies) == 2
    assert strategy.table_strategies[0].table_name == "table1"
    assert strategy.table_strategies[0].strategy_type == TableStrategyTypes.TRUNCATE
    assert strategy.table_strategies[1].table_name == "table1"
    assert strategy.table_strategies[1].strategy_type == TableStrategyTypes.TRUNCATE


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