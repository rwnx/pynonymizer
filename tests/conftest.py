import pytest
from unittest.mock import Mock

from pynonymizer.strategy.database import DatabaseStrategy
from pynonymizer.strategy.table import TruncateTableStrategy, UpdateColumnsTableStrategy
from pynonymizer.strategy.update_column import UniqueEmailUpdateColumnStrategy, UniqueLoginUpdateColumnStrategy, FakeUpdateColumnStrategy, EmptyUpdateColumnStrategy
from pynonymizer.fake import FakeDataType


@pytest.fixture
def simple_strategy_fake_generator():
    return Mock(get_data_type=Mock(return_value=FakeDataType.STRING), get_value=Mock(return_value="TEST_VALUE"))


@pytest.fixture
def simple_strategy_update_fake_column(simple_strategy_fake_generator):
    return FakeUpdateColumnStrategy("column3", simple_strategy_fake_generator, "user_name", where="BANANAS < 3")


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
def simple_strategy_schema_trunc():
    return TruncateTableStrategy("truncate_schema_table", schema="schema")


@pytest.fixture
def simple_strategy(simple_strategy_trunc, simple_strategy_update):
    return DatabaseStrategy([
        simple_strategy_trunc,
        simple_strategy_update
    ])

