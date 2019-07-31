from pynonymizer.database.mssql import MsSqlProvider
from pynonymizer.database.exceptions import DependencyError
import pytest
import pyodbc
from decimal import Decimal
from unittest.mock import patch, Mock, call
from tests.helpers import list_rindex


@pytest.fixture
def provider():
    return MsSqlProvider(None, "DB_USER", "DB_PASS", "DB_NAME")

@pytest.fixture
def provider_with_compression():
    return MsSqlProvider(None, "DB_USER", "DB_PASS", "DB_NAME", backup_compression=True)


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


def test_raise_on_remote_server():
    with pytest.raises(DependencyError):
        MsSqlProvider("192.168.2.1", "username", "password", "dbname")

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

    connect.return_value.execute.assert_any_call(
        'RESTORE DATABASE ? FROM DISK = ? WITH MOVE ? TO ?, MOVE ? TO ?, MOVE ? TO ?, STATS = ?;',
        [
            'DB_NAME', 'test.bak', 'AdventureWorks2016_EXT_Data', 'C:\\DB_NAME_AdventureWorks2016_EXT_Data.mdf',
            'AdventureWorks2016_EXT_Log', 'C:\\DB_NAME_AdventureWorks2016_EXT_Log.ldf', 'AdventureWorks2016_EXT_mod',
            'C:\\DB_NAME_AdventureWorks2016_EXT_mod', 5
        ]
    )


@patch("pyodbc.connect")
def test_dump_database(connect, provider):
    connect.return_value.execute.side_effect = mock_backup_side_effect
    provider.dump_database("test_output.bak")

    connect.return_value.execute.assert_any_call("BACKUP DATABASE ? TO DISK = ? WITH STATS = ?;", ["DB_NAME", "test_output.bak", 5])

@patch("pyodbc.connect")
def test_dump_database_compression(connect, provider_with_compression):
    connect.return_value.execute.side_effect = mock_backup_side_effect
    provider_with_compression.dump_database("test_output.bak")

    connect.return_value.execute.assert_any_call("BACKUP DATABASE ? TO DISK = ? WITH COMPRESSION, STATS = ?;", ["DB_NAME", "test_output.bak", 5])


@patch("pyodbc.connect")
def test_drop_database(connect, provider):
    provider.drop_database()

    connect.return_value.execute.assert_any_call("DROP DATABASE IF EXISTS [DB_NAME];")


@patch("pyodbc.connect")
def test_anonymize(connect, provider, simple_strategy, simple_strategy_fake_generator):
    provider.anonymize_database(simple_strategy)

    execute_calls = connect().execute.mock_calls

    ix_create_seed = execute_calls.index(call('CREATE TABLE [_pynonymizer_seed_fake_data]([user_name] VARCHAR(MAX));'))
    ix_insert_seed_first = execute_calls.index(call('INSERT INTO [_pynonymizer_seed_fake_data]([user_name]) VALUES ( ?);', ['TEST_VALUE']))
    ix_insert_seed_last = list_rindex(execute_calls, call('INSERT INTO [_pynonymizer_seed_fake_data]([user_name]) VALUES ( ?);', ['TEST_VALUE']) )
    ix_trunc_table = execute_calls.index(call('TRUNCATE TABLE [truncate_table];'))
    ix_update_table_1 = execute_calls.index(call("UPDATE [update_table_where_3] SET [column1] = ( SELECT CONCAT(NEWID(), '@', NEWID(), '.com') ),[column2] = ( SELECT NEWID() ) WHERE BANANAS < 5;"))
    ix_update_table_2 = execute_calls.index(call('UPDATE [update_table_where_3] SET [column3] = ( SELECT TOP 1 [user_name] FROM [_pynonymizer_seed_fake_data] ORDER BY NEWID()) WHERE BANANAS < 3;'))
    ix_update_table_3 = execute_calls.index(call("UPDATE [update_table_where_3] SET [column4] = ('');"))
    ix_drop_seed = execute_calls.index(call('DROP TABLE IF EXISTS [_pynonymizer_seed_fake_data];'))

    # seed table create needs to happen before inserting data
    assert ix_create_seed < ix_insert_seed_first

    # last insert of seed data before update anonymize starts
    assert ix_insert_seed_last < ix_trunc_table
    assert ix_insert_seed_last < ix_update_table_1
    assert ix_insert_seed_last < ix_update_table_2
    assert ix_insert_seed_last < ix_update_table_3

    # update anonymize should all be before seed table drop
    assert ix_update_table_1 < ix_drop_seed
    assert ix_update_table_2 < ix_drop_seed
    assert ix_update_table_3 < ix_drop_seed