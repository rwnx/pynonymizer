import unittest
import pytest
import os
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.strategy.database import DatabaseStrategy
from pynonymizer.strategy.table import TruncateTableStrategy
from pynonymizer.database.exceptions import UnsupportedTableStrategyError
from tests.helpers import list_rindex


@patch("pynonymizer.database.mysql.execution", autospec=True)
def test_init_runners_correctly(execution):
    """
    Test the provider inits dependencies with the correct database information
    """
    MySqlProvider("1.2.3.4", "root", "password", "db_name", dump_opts="--test-arg=3")
    execution.MySqlCmdRunner.assert_called_once_with(db_host="1.2.3.4", db_user="root", db_pass="password", db_name="db_name", db_port="3306")
    execution.MySqlDumpRunner.assert_called_once_with(db_host="1.2.3.4", db_user="root", db_pass="password", db_name="db_name", db_port="3306", additional_opts="--test-arg=3")


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
def test_create_database(query_factory, execution):
    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
    provider.create_database()

    # assert that the query factory is called with the db name, and the output is passed to the execute runner
    query_factory.get_create_database.assert_called_once_with("db_name")
    execution.MySqlCmdRunner.return_value.execute.assert_called_once_with(query_factory.get_create_database.return_value)


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
def test_drop_database(query_factory, execution):
    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
    provider.drop_database()

    # assert that the query factory is called with the db name, and the output is passed to the execute runner
    query_factory.get_drop_database.assert_called_once_with("db_name")
    execution.MySqlCmdRunner.return_value.execute.assert_called_once_with(query_factory.get_drop_database.return_value)


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
def test_connection(query_factory, execution):
    # test_connection should return the cmd runner's test output (bool)
    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
    assert provider.test_connection() == execution.MySqlCmdRunner.return_value.test.return_value


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
@patch("pynonymizer.database.mysql.resolve_input")
def test_restore_database(resolve_input, query_factory, execution):
    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
    rand_data = bytes( os.urandom(8193) )
    mock_input = Mock(get_size=Mock(return_value=8193), open=mock_open(read_data=rand_data))
    resolve_input.return_value = mock_input

    provider.restore_database("testfile.bbs")

    # ask for size
    mock_input.get_size.assert_called()
    # open input and read at least once
    mock_input.open.assert_called()
    mock_input.open.return_value.read.assert_called()
    # open, write and flush at least once
    execution.MySqlCmdRunner.return_value.open_batch_processor.assert_called_once_with()
    execution.MySqlCmdRunner.return_value.open_batch_processor.return_value.write.assert_called()
    execution.MySqlCmdRunner.return_value.open_batch_processor.return_value.flush.assert_called()


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
@patch("pynonymizer.database.mysql.resolve_output")
def test_dump_database(resolve_output, query_factory, execution):
    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
    rand_data = bytes( os.urandom(8192) )
    mock_output = Mock(open=mock_open())
    resolve_output.return_value = mock_output

    execution.MySqlDumpRunner.return_value.open_dumper.return_value = MagicMock(read=MagicMock(side_effect=[rand_data, b""]))

    provider.dump_database("testfile.bbs")

    # open output and write at least once
    mock_output.open.assert_called()
    mock_output.open.return_value.write.assert_called()

    # open dumper and read at least once
    execution.MySqlDumpRunner.return_value.open_dumper.assert_called_once_with()
    execution.MySqlDumpRunner.return_value.open_dumper.return_value.read.assert_called()


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
def test_anonymize_database_unsupported_table_strategy(query_factory, execution):
    with pytest.raises(UnsupportedTableStrategyError) as e_info:
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        database_strategy = DatabaseStrategy([
                Mock(table_name="table1", strategy_type="DEFINITELY_NOT_A_SUPPORTED_STRATEGY_TYPE"),
        ])
        provider.anonymize_database(database_strategy)


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
def test_before_script_run(query_factory, execution):
    manager = Mock()
    manager.attach_mock(execution, "execution")

    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
    database_strategy = DatabaseStrategy(table_strategies=[
            TruncateTableStrategy("table1")
        ],
        before_scripts=["SELECT `before` FROM `before_table`;"]
    )

    provider.anonymize_database(database_strategy)

    truncate_call_index = manager.mock_calls.index(call.execution.MySqlCmdRunner().db_execute(query_factory.get_truncate_table.return_value))
    before_script_call_index = manager.mock_calls.index( call.execution.MySqlCmdRunner().db_execute("SELECT `before` FROM `before_table`;") )

    # before script should be before any anonymization happens (truncate)
    assert before_script_call_index < truncate_call_index


@patch("pynonymizer.database.mysql.execution", autospec=True)
@patch("pynonymizer.database.mysql.query_factory", autospec=True)
def test_after_script_run(query_factory,execution):
    manager = Mock()
    manager.attach_mock(execution, "execution")

    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
    database_strategy = DatabaseStrategy(table_strategies=[
            TruncateTableStrategy("table1")
        ],
        after_scripts=["SELECT `after` FROM `after_table`;"]
    )
    provider.anonymize_database(database_strategy)

    truncate_call_index = manager.mock_calls.index(call.execution.MySqlCmdRunner().db_execute(query_factory.get_truncate_table.return_value))
    after_script_call_index = manager.mock_calls.index( call.execution.MySqlCmdRunner().db_execute("SELECT `after` FROM `after_table`;") )

    # after script should be called after anonymization
    assert truncate_call_index < after_script_call_index


@patch("pynonymizer.database.mysql.execution")
@patch("pynonymizer.database.mysql.query_factory")
def test_anonymize_database(query_factory, execution, simple_strategy, simple_strategy_update_fake_column, simple_strategy_update):
    manager = Mock()
    manager.attach_mock(execution, "execution")

    provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")

    provider.anonymize_database(simple_strategy)

    seed_table_qualifier_map = ["_pynonymizer_seed_fake_data", {"user_name": simple_strategy_update_fake_column}]

    # get_create_seed_table( seed table name, qualifier map)
    query_factory.get_create_seed_table.assert_called_once_with(*seed_table_qualifier_map)

    # seed table should be called with the qual map 150 times
    query_factory.get_insert_seed_row.assert_has_calls( ([call(*seed_table_qualifier_map)] * 150) )

    query_factory.get_truncate_table.assert_called_once_with("truncate_table")
    query_factory.get_update_table.assert_called_once_with("_pynonymizer_seed_fake_data", simple_strategy_update)
    query_factory.get_drop_seed_table.assert_called_once_with("_pynonymizer_seed_fake_data")

    # anonymize basic order checks
    ix_create_seed = manager.mock_calls.index(call.execution.MySqlCmdRunner().db_execute(query_factory.get_create_seed_table()))
    ix_insert_seed_first = manager.mock_calls.index(call.execution.MySqlCmdRunner().db_execute(query_factory.get_insert_seed_row()))
    ix_insert_seed_last =  list_rindex(manager.mock_calls, call.execution.MySqlCmdRunner().db_execute(query_factory.get_insert_seed_row()))
    ix_trunc_table = manager.mock_calls.index(call.execution.MySqlCmdRunner().db_execute(query_factory.get_truncate_table()))
    ix_update_table = manager.mock_calls.index(call.execution.MySqlCmdRunner().db_execute(query_factory.get_update_table()))
    ix_drop_seed = manager.mock_calls.index(call.execution.MySqlCmdRunner().db_execute(query_factory.get_drop_seed_table()))

    assert ix_create_seed < ix_insert_seed_first
    assert ix_insert_seed_last < ix_trunc_table
    assert ix_insert_seed_last < ix_update_table
    assert ix_update_table < ix_drop_seed
