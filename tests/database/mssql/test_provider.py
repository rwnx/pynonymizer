from pynonymizer.database.mssql import MsSqlProvider
from pynonymizer.database.exceptions import DependencyError
import pytest
import pyodbc
from decimal import Decimal
from unittest.mock import patch, Mock, call
from tests.helpers import list_rindex


@pytest.fixture
def provider():
    return MsSqlProvider(
        None, "DB_USER", "DB_PASS", "DB_NAME", driver="testdriver", seed_rows=150
    )


@pytest.fixture
def provider_with_compression():
    return MsSqlProvider(
        None,
        "DB_USER",
        "DB_PASS",
        "DB_NAME",
        driver="testdriver",
        backup_compression=True,
        seed_rows=150,
    )


def mock_restore_side_effect(statement, *args, **kwargs):
    if statement.strip().startswith("RESTORE FILELISTONLY"):
        filelist = Mock()
        filelist.fetchall.return_value = [
            (
                "AdventureWorks2016_EXT_Data",
                "C:\\Program Files\\Microsoft SQL Server\\MSSQL13.MSSQL2016RTM\\MSSQL\\DATA\\AdventureWorks2016_EXT_Data.mdf",
                "D",
                "PRIMARY",
                405078016,
                35184372080640,
                1,
                Decimal("0"),
                Decimal("0"),
                "78D8A94F-4CFF-4ED0-9846-3AF3BE2F1C7D",
                Decimal("0"),
                Decimal("0"),
                394002432,
                512,
                1,
                None,
                Decimal("108000000652300212"),
                "A7CE522E-427E-4375-8054-DA6B304B6C4F",
                False,
                True,
                None,
                None,
            ),
            (
                "AdventureWorks2016_EXT_Log",
                "C:\\Program Files\\Microsoft SQL Server\\MSSQL13.MSSQL2016RTM\\MSSQL\\DATA\\AdventureWorks2016_EXT_Log.ldf",
                "L",
                None,
                186646528,
                2199023255552,
                2,
                Decimal("0"),
                Decimal("0"),
                "9B6653F1-815D-4064-82F6-C43D81CABD61",
                Decimal("0"),
                Decimal("0"),
                0,
                512,
                0,
                None,
                Decimal("0"),
                "00000000-0000-0000-0000-000000000000",
                False,
                True,
                None,
                None,
            ),
            (
                "AdventureWorks2016_EXT_mod",
                "C:\\Program Files\\Microsoft SQL Server\\MSSQL13.MSSQL2016RTM\\MSSQL\\DATA\\AdventureWorks2016_EXT_mod",
                "S",
                "AdventureWorks2016_EXT_mod",
                0,
                0,
                65537,
                Decimal("43000002114900003"),
                Decimal("0"),
                "E3B5DA3E-E186-491A-A723-E4A6852C0B55",
                Decimal("0"),
                Decimal("0"),
                1025310720,
                512,
                2,
                None,
                Decimal("108000000652300212"),
                "A7CE522E-427E-4375-8054-DA6B304B6C4F",
                False,
                True,
                None,
                None,
            ),
        ]
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
@patch(
    "pyodbc.drivers",
    return_value=[
        "SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server Native Client RDA 11.0",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "Microsoft Access Driver (*.mdb, *.accdb)",
        "Microsoft Excel Driver (*.xls, *.xlsx, *.xlsm, *.xlsb)",
        "Microsoft Access Text Driver (*.txt, *.csv)",
    ],
)
def test_detect_drivers__when_many_drivers__should_connect_with_highest_numbered(
    drivers, connect
):
    provider = MsSqlProvider(
        "192.168.2.1", "username", "password", "dbname", seed_rows=150
    )
    provider.drop_database()

    connect.assert_any_call(
        driver="{ODBC Driver 17 for SQL Server}",
        server="192.168.2.1,1433",
        uid="username",
        pwd="password",
        autocommit=True,
    )


@patch("pyodbc.drivers", return_value=[])
def test_detect_drivers__when_no_drivers__raises_dependencyerror(drivers):
    with pytest.raises(DependencyError):
        MsSqlProvider("192.168.2.1", "username", "password", "dbname", seed_rows=150)


def test_raise_on_remote_server_backup():
    provider = MsSqlProvider(
        "192.168.2.1", "username", "password", "dbname", driver="driver", seed_rows=150
    )
    with pytest.raises(DependencyError):
        provider.dump_database("./output.bak")


def test_raise_on_remote_server_restore():
    provider = MsSqlProvider(
        "192.168.2.1", "username", "password", "dbname", driver="driver", seed_rows=150
    )
    with pytest.raises(DependencyError):
        provider.restore_database("./local.bak")


@patch("pyodbc.connect")
def test_create_database_noop(connect, provider):
    """
    create_database should do nothing.
    """
    provider.create_database()

    connect.assert_not_called()
    connect.return_value.execute.assert_not_called()


@patch("pyodbc.connect")
def test_restore_database(connect, provider):
    connect.return_value.execute.side_effect = mock_restore_side_effect
    provider.restore_database("test.bak")

    connect.return_value.execute.assert_any_call(
        "RESTORE DATABASE ? FROM DISK = ? WITH MOVE ? TO ?, MOVE ? TO ?, MOVE ? TO ?, STATS = ?;",
        [
            "DB_NAME",
            "test.bak",
            "AdventureWorks2016_EXT_Data",
            "C:\\DB_NAME_AdventureWorks2016_EXT_Data.mdf",
            "AdventureWorks2016_EXT_Log",
            "C:\\DB_NAME_AdventureWorks2016_EXT_Log.ldf",
            "AdventureWorks2016_EXT_mod",
            "C:\\DB_NAME_AdventureWorks2016_EXT_mod",
            5,
        ],
    )


@patch("pyodbc.connect")
def test_dump_database(connect, provider):
    connect.return_value.execute.side_effect = mock_backup_side_effect
    provider.dump_database("test_output.bak")

    connect.return_value.execute.assert_any_call(
        "BACKUP DATABASE ? TO DISK = ? WITH STATS = ?;",
        ["DB_NAME", "test_output.bak", 5],
    )


@patch("pyodbc.connect")
def test_dump_database_compression(connect, provider_with_compression):
    connect.return_value.execute.side_effect = mock_backup_side_effect
    provider_with_compression.dump_database("test_output.bak")

    connect.return_value.execute.assert_any_call(
        "BACKUP DATABASE ? TO DISK = ? WITH COMPRESSION, STATS = ?;",
        ["DB_NAME", "test_output.bak", 5],
    )


@patch("pyodbc.connect")
def test_drop_database(connect, provider):
    provider.drop_database()

    connect.return_value.execute.assert_any_call("DROP DATABASE IF EXISTS [DB_NAME];")


@patch("pyodbc.connect")
def test_anonymize(connect, provider, simple_strategy, simple_strategy_fake_generator):
    provider.anonymize_database(simple_strategy)

    execute_calls = connect().execute.mock_calls

    ix_create_seed = execute_calls.index(
        call("CREATE TABLE [_pynonymizer_seed_fake_data]([user_name] VARCHAR(MAX));")
    )
    ix_insert_seed_first = execute_calls.index(
        call(
            "INSERT INTO [_pynonymizer_seed_fake_data]([user_name]) VALUES ( ?);",
            ["TEST_VALUE"],
        )
    )
    ix_insert_seed_last = list_rindex(
        execute_calls,
        call(
            "INSERT INTO [_pynonymizer_seed_fake_data]([user_name]) VALUES ( ?);",
            ["TEST_VALUE"],
        ),
    )
    ix_trunc_table = execute_calls.index(call("TRUNCATE TABLE [truncate_table];"))
    ix_delete_table = execute_calls.index(call("DELETE FROM [delete_table];"))
    ix_update_table_1 = execute_calls.index(
        call(
            "SET ANSI_WARNINGS off; UPDATE [update_table_where_3] SET [column1] = ( SELECT CONCAT(NEWID(), '@', NEWID(), '.com') ),[column2] = ( SELECT NEWID() ) WHERE BANANAS < 5; SET ANSI_WARNINGS on;"
        )
    )
    ix_update_table_2 = execute_calls.index(
        call(
            "SET ANSI_WARNINGS off; UPDATE [update_table_where_3] SET [column3] = ( SELECT TOP 1 [user_name] FROM [_pynonymizer_seed_fake_data] WHERE [update_table_where_3].[column3] LIKE '%' OR [update_table_where_3].[column3] IS NULL ORDER BY NEWID()) WHERE BANANAS < 3; SET ANSI_WARNINGS on;"
        )
    )
    ix_update_table_3 = execute_calls.index(
        call(
            "SET ANSI_WARNINGS off; UPDATE [update_table_where_3] SET [column4] = (''); SET ANSI_WARNINGS on;"
        )
    )
    ix_drop_seed = execute_calls.index(
        call("DROP TABLE IF EXISTS [_pynonymizer_seed_fake_data];")
    )

    # seed table create needs to happen before inserting data
    assert ix_create_seed < ix_insert_seed_first

    # last insert of seed data before update anonymize starts
    assert ix_insert_seed_last < ix_trunc_table
    assert ix_insert_seed_last < ix_delete_table
    assert ix_insert_seed_last < ix_update_table_1
    assert ix_insert_seed_last < ix_update_table_2
    assert ix_insert_seed_last < ix_update_table_3

    # update anonymize should all be before seed table drop
    assert ix_update_table_1 < ix_drop_seed
    assert ix_update_table_2 < ix_drop_seed
    assert ix_update_table_3 < ix_drop_seed
