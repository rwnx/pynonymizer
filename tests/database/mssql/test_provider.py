from pynonymizer.database.mssql import MsSqlProvider
import pytest
import pyodbc
from decimal import Decimal
from unittest.mock import patch, Mock, call


@pytest.fixture
def provider():
    return MsSqlProvider(None, "DB_USER", "DB_PASS", "DB_NAME")


def mock_restore_side_effect(statement, *args, **kwargs):
    if statement.strip().startswith("RESTORE FILELISTONLY"):
        filelist = Mock()
        filelist.fetchall.return_value = [('AdventureWorks2016_EXT_Data', 'C:\\Program Files\\Microsoft SQL Server\\MSSQL13.MSSQL2016RTM\\MSSQL\\DATA\\AdventureWorks2016_EXT_Data.mdf', 'D', 'PRIMARY', 405078016, 35184372080640, 1, Decimal('0'), Decimal('0'), '78D8A94F-4CFF-4ED0-9846-3AF3BE2F1C7D', Decimal('0'), Decimal('0'), 394002432, 512, 1, None, Decimal('108000000652300212'), 'A7CE522E-427E-4375-8054-DA6B304B6C4F', False, True, None, None), ('AdventureWorks2016_EXT_Log', 'C:\\Program Files\\Microsoft SQL Server\\MSSQL13.MSSQL2016RTM\\MSSQL\\DATA\\AdventureWorks2016_EXT_Log.ldf', 'L', None, 186646528, 2199023255552, 2, Decimal('0'), Decimal('0'), '9B6653F1-815D-4064-82F6-C43D81CABD61', Decimal('0'), Decimal('0'), 0, 512, 0, None, Decimal('0'), '00000000-0000-0000-0000-000000000000', False, True, None, None), ('AdventureWorks2016_EXT_mod', 'C:\\Program Files\\Microsoft SQL Server\\MSSQL13.MSSQL2016RTM\\MSSQL\\DATA\\AdventureWorks2016_EXT_mod', 'S', 'AdventureWorks2016_EXT_mod', 0, 0, 65537, Decimal('43000002114900003'), Decimal('0'), 'E3B5DA3E-E186-491A-A723-E4A6852C0B55', Decimal('0'), Decimal('0'), 1025310720, 512, 2, None, Decimal('108000000652300212'), 'A7CE522E-427E-4375-8054-DA6B304B6C4F', False, True, None, None)]
        return filelist
    if statement.strip().startswith("RESTORE DATABASE"):
        restore = Mock()
        restore.nextset.side_effect = [True, True, False]
        return restore
    if statement.strip().startswith("SELECT"):
        selectvar = Mock()
        selectvar.fetchone.return_value = ("C:\\test.mdf",)
        return selectvar

    return Mock()


def mock_backup_side_effect(statement, *args, **kwargs):
    if statement.strip().startswith("BACKUP DATABASE"):
        backup_mock = Mock()
        backup_mock.nextset.side_effect = [True, True, False]
        return backup_mock

    return Mock()


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
    connect.return_value.execute.side_effect = mock_restore_side_effect
    provider.restore_database("test.bak")

    print(connect.return_value.execute.call_args_list)
    connect.return_value.execute.assert_any_call( 'RESTORE DATABASE ? FROM DISK = ? WITH MOVE ? TO ?, MOVE ? TO ?, MOVE ? TO ?, STATS = ?;', ['DB_NAME', 'test.bak', 'AdventureWorks2016_EXT_Data', 'C:\\DB_NAME_AdventureWorks2016_EXT_Data.mdf', 'AdventureWorks2016_EXT_Log', 'C:\\DB_NAME_AdventureWorks2016_EXT_Log.ldf', 'AdventureWorks2016_EXT_mod', 'C:\\DB_NAME_AdventureWorks2016_EXT_mod', 5])


@patch("pyodbc.connect")
def test_dump_database(connect, provider):
    connect.return_value.execute.side_effect = mock_backup_side_effect
    provider.dump_database("test_output.bak")

    connect.return_value.execute.assert_any_call("BACKUP DATABASE ? TO DISK = ? WITH STATS = ?;", ["DB_NAME", "test_output.bak", 5])


@patch("pyodbc.connect")
def test_drop_database(connect, provider):
    provider.drop_database()

    connect.return_value.execute.assert_any_call("DROP DATABASE IF EXISTS [DB_NAME];")