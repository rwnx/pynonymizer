from pynonymizer.database.mssql import MsSqlProvider
import pytest
from unittest.mock import patch, Mock


@pytest.fixture
def provider():
    return MsSqlProvider("DB_HOST", "DB_USER", "DB_PASS", "DB_NAME")


@patch("pyodbc.connect")
def test_create_database_noop(connect, provider):
    """
    create_database should do nothing.
    """
    provider.create_database()
    connect.assert_not_called()


def test_test_connection():
    pass

def test_restore_database():
    pass

def test_dump_database():
    pass

def test_drop_database(provider):
    pass