import pytest
from pynonymizer.database.exceptions import DatabaseProviderError, MissingPrerequisiteError, UnsupportedTableStrategyError, UnsupportedColumnStrategyError


def test_database_provider_error():
    error = DatabaseProviderError()


def test_missing_prerequisite_error():
    error = MissingPrerequisiteError("error message")


def test_unsupported_table_strategy():
    error = UnsupportedTableStrategyError("error message")


def test_unsupport_column_strategy_error():
    error = UnsupportedColumnStrategyError("COLUMN_STRATEGY_TYPE")