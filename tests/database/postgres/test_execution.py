import pytest
import unittest
from unittest.mock import patch, Mock
from pynonymizer.database.exceptions import DependencyError
from pynonymizer.database.postgres.execution import PSqlCmdRunner, PSqlDumpRunner
from tests.helpers import SuperdictOf
import subprocess


@patch("shutil.which", Mock(return_value=None))
class NoExecutablesInPathTests(unittest.TestCase):
    def test_dump_runner_missing_mysqldump(self):
        with pytest.raises(DependencyError):
            PSqlDumpRunner("1.2.3.4", "user", "password", "name")


    def test_cmd_runner_missing_mysql(self):
        with pytest.raises(DependencyError):
            PSqlCmdRunner("1.2.3.4", "user", "password", "name")


@patch("subprocess.Popen")
@patch("subprocess.check_output")
@patch("shutil.which", Mock(return_value="fake/path/to/executable"))
class DumperTests(unittest.TestCase):
    def test_open_dumper(self, check_output, popen):
        dump_runner = PSqlDumpRunner("1.2.3.4", "db_user", "db_password", "db_name")
        open_result = dump_runner.open_dumper()

        # dumper should open a process for the current db dump, piping stdout for processing
        popen.assert_called_with(['pg_dump', '--host', '1.2.3.4', '--username', 'db_user', 'db_name'],
                                 env=SuperdictOf({"PGPASSWORD": "db_password"}), stdout=subprocess.PIPE)

        # dumper should return the stdout of that process
        assert open_result == popen.return_value.stdout


@patch("subprocess.Popen")
@patch("subprocess.check_output")
@patch("shutil.which", Mock(return_value="fake/path/to/executable"))
class CmdTests(unittest.TestCase):
    def test_open_batch_processor(self, check_output, popen):
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        open_result = cmd_runner.open_batch_processor()

        # dumper should open a process for the current db dump, piping stdout for processing
        popen.assert_called_with(["psql", "--host", "1.2.3.4", "--username", "db_user", "--dbname", "db_name", "--quiet"],
                                 env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                 stdin=subprocess.PIPE)

        # dumper should return the stdin of that process
        assert open_result == popen.return_value.stdin

    def test_execute(self, check_output, popen):
        """
        execute should execute an arbitrary statement with valid args
        """
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.execute("SELECT `column` from `table`;")

        check_output.assert_called_with(["psql", "--host", "1.2.3.4", "--username", "db_user", "--command",
                                         "SELECT `column` from `table`;"],
                                        env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                        )

    def test_execute_list(self, check_output, popen):
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.execute(["SELECT `column` from `table`;", "SELECT `column2` from `table2`;"])

        check_output.assert_any_call(["psql", "--host", "1.2.3.4", "--username", "db_user", "--command",
                                         "SELECT `column` from `table`;"],
                                     env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                     )

        check_output.assert_any_call(["psql", "--host", "1.2.3.4", "--username", "db_user", "--command",
                                         "SELECT `column2` from `table2`;"],
                                     env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                     )

    def test_db_execute(self, check_output, popen):
        """
        execute should execute an arbitrary statement with valid args
        """
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.db_execute("SELECT `column` from `table`;")

        check_output.assert_called_with(["psql", "--host", "1.2.3.4", "--username", "db_user", "--dbname", "db_name", "--command", "SELECT `column` from `table`;"],
                                        env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                        )

    def test_db_execute_list(self, check_output, popen):
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        execute_result = cmd_runner.db_execute(["SELECT `column` from `table`;", "SELECT `column2` from `table2`;"])

        check_output.assert_any_call(["psql", "--host", "1.2.3.4", "--username", "db_user", "--dbname", "db_name", "--command",
                                      "SELECT `column` from `table`;"],
                                     env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                     )
        check_output.assert_any_call(["psql", "--host", "1.2.3.4", "--username", "db_user", "--dbname", "db_name", "--command",
                                      "SELECT `column2` from `table2`;"],
                                     env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                     )

    def test_get_single_result(self, check_output, popen):
        """
        execute should execute an arbitrary statement and return the decoded, no-column result
        """
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        single_result = cmd_runner.get_single_result("SELECT `column` from `table`;")

        check_output.assert_called_with(["psql", "--host", "1.2.3.4", "--username", "db_user", "--dbname", "db_name", "-tA", "--command", "SELECT `column` from `table`;"],
                                        env=SuperdictOf({"PGPASSWORD": "db_password"}),
                                        )
        assert single_result == check_output.return_value.decode.return_value

    def test_connection_ok(self, check_output, popen):
        """
        When subprocess returns no errors, test should return true
        """
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        assert cmd_runner.test() is True

    def test_connection_bad(self, check_output, popen):
        """
        When subprocess throws calledProcessError, test should return false
        """
        check_output.side_effect = subprocess.CalledProcessError(1, "fakecmd")
        cmd_runner = PSqlCmdRunner("1.2.3.4", "db_user", "db_password", "db_name")
        assert cmd_runner.test() is False
