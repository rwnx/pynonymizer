import pytest
import unittest
from unittest.mock import patch, Mock
from pynonymizer.database.exceptions import DependencyError
from pynonymizer.database.mysql.execution import MySqlDumpRunner, MySqlCmdRunner
import subprocess


@patch("shutil.which", Mock(return_value=None))
class NoExecutablesInPathTests(unittest.TestCase):
    def test_dump_runner_missing_mysqldump(self):
        with pytest.raises(DependencyError):
            MySqlDumpRunner("1.2.3.4", "user", "password", "name")


    def test_cmd_runner_missing_mysql(self):
        with pytest.raises(DependencyError):
            MySqlCmdRunner("1.2.3.4", "user", "password", "name")


@patch("subprocess.Popen")
@patch("subprocess.check_output")
@patch("shutil.which", Mock(return_value="fake/path/to/executable"))
class DumperTests(unittest.TestCase):
    def test_open_dumper(self, check_output, popen):
        dump_runner = MySqlDumpRunner("1.2.3.4", "db_user", "db_password", "db_name")
        open_result = dump_runner.open_dumper()

        # dumper should open a process for the current db dump, piping stdout for processing
        popen.assert_called_with(["mysqldump", "--host", "1.2.3.4", "--user", "db_user", "-pdb_password", "db_name"], stdout=subprocess.PIPE)

        # dumper should return the stdout of that process
        assert open_result == popen.return_value.stdout


@patch("subprocess.Popen")
@patch("subprocess.check_output")
@patch("shutil.which", Mock(return_value="fake/path/to/executable"))
class CmdTests(unittest.TestCase):
    def test_open_batch_processor(self, check_output, popen):
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        open_result = cmd_runner.open_batch_processor()

        # dumper should open a process for the current db dump, piping stdout for processing
        popen.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "db_name"], stdin=subprocess.PIPE)

        # dumper should return the stdin of that process
        assert open_result == popen.return_value.stdin

    def test_execute(self, check_output, popen):
        """
        execute should execute an arbitrary statement with valid args
        """
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.execute("SELECT `column` from `table`;")

        check_output.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "--execute",
                                         "SELECT `column` from `table`;"])

    def test_execute_list(self, check_output, popen):
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.execute(["SELECT `column` from `table`;", "SELECT `column2` from `table2`;"])

        check_output.assert_any_call(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "--execute",
                                         "SELECT `column` from `table`;"])

        check_output.assert_any_call(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "--execute",
                                         "SELECT `column2` from `table2`;"])

    def test_db_execute(self, check_output, popen):
        """
        execute should execute an arbitrary statement with valid args
        """
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.db_execute("SELECT `column` from `table`;")

        check_output.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "db_name", "--execute", "SELECT `column` from `table`;"])

    def test_db_execute_list(self, check_output, popen):
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.db_execute(["SELECT `column` from `table`;", "SELECT `column2` from `table2`;"])

        check_output.assert_any_call(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "db_name", "--execute",
                                      "SELECT `column` from `table`;"])
        check_output.assert_any_call(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "db_name", "--execute",
                                      "SELECT `column2` from `table2`;"])

    def test_get_single_result(self, check_output, popen):
        """
        execute should execute an arbitrary statement and return the decoded, no-column result
        """
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        single_result = cmd_runner.get_single_result("SELECT `column` from `table`;")

        check_output.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "db_user", "-pdb_password", "-sN", "db_name", "--execute", "SELECT `column` from `table`;"])
        assert single_result == check_output.return_value.decode.return_value

    def test_connection_ok(self, check_output, popen):
        """
        When subprocess returns no errors, test should return true
        """
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        assert cmd_runner.test() is True

    def test_connection_bad(self, check_output, popen):
        """
        When subprocess throws calledProcessError, test should return false
        """
        check_output.side_effect = subprocess.CalledProcessError(1, "fakecmd")
        cmd_runner = MySqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        assert cmd_runner.test() is False
