import pytest
from unittest.mock import Mock

from pynonymizer.strategy.database import DatabaseStrategy
from pynonymizer.strategy.table import TruncateTableStrategy, UpdateColumnsTableStrategy
from pynonymizer.strategy.update_column import UniqueEmailUpdateColumnStrategy, UniqueLoginUpdateColumnStrategy, FakeUpdateColumnStrategy, EmptyUpdateColumnStrategy

@pytest.fixture
def simple_strategy_update_fake_column():
    return FakeUpdateColumnStrategy("column3", Mock(), "user_name", where="BANANAS < 3")


@pytest.fixture
def simple_strategy_update(simple_strategy_update_fake_column):
    return UpdateColumnsTableStrategy("update_table_where_3", [
            UniqueEmailUpdateColumnStrategy("column1", where="BANANAS < 5"),
            UniqueLoginUpdateColumnStrategy("column2", where="BANANAS < 5"),
            simple_strategy_update_fake_column,
            EmptyUpdateColumnStrategy("column4")
        ])


@pytest.fixture
def simple_strategy_trunc():
    return TruncateTableStrategy("truncate_table")


@pytest.fixture
def simple_strategy(simple_strategy_trunc, simple_strategy_update):
    return DatabaseStrategy([
        simple_strategy_trunc,
        simple_strategy_update
    ])