import unittest
import os
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from pynonymizer.database.mysql import MySqlProvider
import pynonymizer.strategy.database
import pynonymizer.strategy.table
import pynonymizer.strategy.update_column
import pynonymizer.input
import pynonymizer.output


class MySqlProviderInitTest(unittest.TestCase):
    @patch("pynonymizer.database.mysql.provider.execution", autospec=True)
    def test_init_runners_correctly(self, exec):
        """
        Test the provider inits dependencies with the correct database information
        """
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        exec.MySqlCmdRunner.assert_called_once_with("1.2.3.4", "root", "password", "db_name")
        exec.MySqlDumpRunner.assert_called_once_with("1.2.3.4", "root", "password", "db_name")


@patch("pynonymizer.database.mysql.provider.execution", autospec=True)
@patch("pynonymizer.database.mysql.provider.query_factory", autospec=True)
class DatabaseQueryExecTests(unittest.TestCase):
    def test_create_database(self, query_factory, execution):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        provider.create_database()

        # assert that the query factory is called with the db name, and the output is passed to the execute runner
        query_factory.get_create_database.assert_called_once_with("db_name")
        execution.MySqlCmdRunner.return_value.execute.assert_called_once_with(query_factory.get_create_database.return_value)

    def test_drop_database(self, query_factory, execution):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        provider.drop_database()

        # assert that the query factory is called with the db name, and the output is passed to the execute runner
        query_factory.get_drop_database.assert_called_once_with("db_name")
        execution.MySqlCmdRunner.return_value.execute.assert_called_once_with(query_factory.get_drop_database.return_value)

    def test_connection(self, query_factory, execution):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        # test_connection should return the cmd runner's test output (bool)
        self.assertEqual( provider.test_connection(), execution.MySqlCmdRunner.return_value.test.return_value )

    def test_restore_database(self, query_factory, execution):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        rand_data = bytes( os.urandom(8193) )
        mock_input = Mock(get_size=Mock(return_value=8193), open=mock_open(read_data=rand_data))

        provider.restore_database(mock_input)

        # ask for size
        mock_input.get_size.assert_called()
        # open input and read at least once
        mock_input.open.assert_called()
        mock_input.open.return_value.read.assert_called()
        # open, write and flush at least once
        execution.MySqlCmdRunner.return_value.open_batch_processor.assert_called_once_with()
        execution.MySqlCmdRunner.return_value.open_batch_processor.return_value.write.assert_called()
        execution.MySqlCmdRunner.return_value.open_batch_processor.return_value.flush.assert_called()

    def test_dump_database(self, query_factory, execution):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        rand_data = bytes( os.urandom(8192) )
        mock_output = Mock(open=mock_open())

        execution.MySqlDumpRunner.return_value.open_dumper.return_value = MagicMock(read=MagicMock(side_effect=[rand_data, b""]))

        provider.dump_database(mock_output)

        # open output and write at least once
        mock_output.open.assert_called()
        mock_output.open.return_value.write.assert_called()

        # open dumper and read at least once
        execution.MySqlDumpRunner.return_value.open_dumper.assert_called_once_with()
        execution.MySqlDumpRunner.return_value.open_dumper.return_value.read.assert_called()

