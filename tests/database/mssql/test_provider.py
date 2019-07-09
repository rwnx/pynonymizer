from pynonymizer.database.mssql import MsSqlProvider
import pytest
import pyodbc
from unittest.mock import patch, Mock


@pytest.fixture
def provider():
    return MsSqlProvider(None, "DB_USER", "DB_PASS", "DB_NAME")


@patch("pyodbc.connect")
def test_create_database_noop(connect, provider):
    """
    create_database should do nothing.
    """
    provider.create_database()

    connect.assert_not_called()
    connect.return_value.execute.assert_not_called()


@patch("pyodbc.connect")
def test_test_connection(connect, provider):
    good_connection = provider.test_connection()

    assert good_connection is True
    connect.return_value.execute.assert_called_with("SELECT @@VERSION;")


@patch("pyodbc.connect")
def test_test_connection_fail(connect, provider):
    connect.return_value.execute.side_effect = pyodbc.OperationalError()

    good_connection = provider.test_connection()

    assert good_connection is False
    connect.return_value.execute.assert_called_with("SELECT @@VERSION;")


@patch("pyodbc.connect")
def test_restore_database(connect, provider):
    pass

def test_dump_database():
    pass

def test_drop_database(provider):
    pass