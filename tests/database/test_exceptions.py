import pytest
from pynonymizer.database.exceptions import DatabaseProviderError, DependencyError, UnsupportedTableStrategyError, UnsupportedColumnStrategyError


def test_database_provider_error():
    error = DatabaseProviderError()


def test_dependency_error():
    error = DependencyError("mysqldump", "error message")
    assert error.name == "mysqldump"


def test_unsupported_table_strategy():
    error = UnsupportedTableStrategyError("error message")


def test_unsupport_column_strategy_error():
    error = UnsupportedColumnStrategyError("COLUMN_STRATEGY_TYPE")
