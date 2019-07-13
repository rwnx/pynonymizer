import pytest
import unittest
from unittest.mock import Mock
from pynonymizer.strategy.update_column import (
    UpdateColumnStrategyTypes,
    EmptyUpdateColumnStrategy,
    UniqueLoginUpdateColumnStrategy,
    UniqueEmailUpdateColumnStrategy,
    LiteralUpdateColumnStrategy,
    FakeUpdateColumnStrategy
)

"""
Tests for making sure strategies are built in the way that we need them to be
Particularly, behaviour surrounding args and arg validation, and strategy-wide constraints (like the `where` option!)
"""

def test_empty():
    empty = EmptyUpdateColumnStrategy(column_name="empty_column")
    assert empty.strategy_type == UpdateColumnStrategyTypes.EMPTY
    assert empty.where_condition == None


def test_empty_where():
    empty_where = EmptyUpdateColumnStrategy(column_name="empty_column", where="`cheese` = 'gouda'")

    assert empty_where.strategy_type == UpdateColumnStrategyTypes.EMPTY
    assert empty_where.where_condition == "`cheese` = 'gouda'"


def test_ulogin():
    ulogin = UniqueLoginUpdateColumnStrategy(column_name="column_name")

    assert ulogin.strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN
    assert ulogin.where_condition == None


def test_ulogin_where():
    ulogin_where = UniqueLoginUpdateColumnStrategy(column_name="column_name",where="`cheese` = 'edam'")

    assert ulogin_where.strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN
    assert ulogin_where.where_condition == "`cheese` = 'edam'"


def test_uemail():
    uemail = UniqueEmailUpdateColumnStrategy(column_name="column_name")

    assert uemail.strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL
    assert uemail.where_condition == None


def test_uemail_where():
    uemail = UniqueEmailUpdateColumnStrategy(column_name="column_name",where="`cheese` = 'gouda'")

    assert uemail.strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL
    assert uemail.where_condition == "`cheese` = 'gouda'"


def test_literal():
    literal = LiteralUpdateColumnStrategy(column_name="column_name",value="52")

    assert literal.strategy_type == UpdateColumnStrategyTypes.LITERAL
    assert literal.where_condition == None
    assert literal.value == "52"


def test_literal_where():
    literal_where = LiteralUpdateColumnStrategy(column_name="column_name",value="RAND()", where="cake = 'death' OR gravel > 3")

    assert literal_where.strategy_type == UpdateColumnStrategyTypes.LITERAL
    assert literal_where.where_condition == "cake = 'death' OR gravel > 3"
    assert literal_where.value == "RAND()"


def test_fake_update():
    fake_column_generator = Mock()
    fake_update = FakeUpdateColumnStrategy(column_name="column_name",fake_column_generator=fake_column_generator, fake_type="company_email")

    assert fake_update.strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE
    assert fake_update.value == fake_column_generator.get_value("company_email")
    assert fake_update.data_type == fake_column_generator.get_data_type("company_email")
    assert fake_update.fake_type == "company_email"


def test_fake_update_where():
    fake_column_generator = Mock()
    fake_update_where = FakeUpdateColumnStrategy(column_name="column_name",fake_column_generator=fake_column_generator, fake_type="company_email", where="chickens = 1")

    assert fake_update_where.strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE
    assert fake_update_where.value == fake_column_generator.get_value("company_email")
    assert fake_update_where.data_type == fake_column_generator.get_data_type("company_email")
    assert fake_update_where.fake_type == "company_email"
    assert fake_update_where.where_condition == "chickens = 1"

