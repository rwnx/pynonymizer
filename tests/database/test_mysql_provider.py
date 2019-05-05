import unittest
from unittest.mock import Mock, patch, MagicMock, call

from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.database.exceptions import MissingPrerequisiteError
from pynonymizer.fake import FakeColumn
import datetime

from subprocess import CalledProcessError

class MySqlProviderInitTest(unittest.TestCase):
    """
    These tests are fragile and rely on the actual SQL the provider is going to run.
    for more robustness, it might be more prudent to rely on some kind of sql parsing, or pattern matching,
    so minor changes (like whitespace) don't break all the tests.
    """
    @patch("pynonymizer.database.mysql.MySqlDumpRunner", autospec=True)
    @patch("pynonymizer.database.mysql.MySqlCmdRunner", autospec=True)
    def test_init_runners_correctly(self, runner, dumper):
        """
        Test the provider inits dependencies with the correct database information
        """
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        runner.assert_called_once_with("1.2.3.4", "root", "password", "db_name")
        dumper.assert_called_once_with("1.2.3.4", "root", "password", "db_name")

@patch("shutil.which", Mock(return_value="/usr/bin/mysql"))
class MySqlProviderCreateDatabaseTests(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_create_database(self, check_mock):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        provider.create_database()
        check_mock.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "root", "-ppassword", "--execute", "CREATE DATABASE `db_name`;"])


@patch("shutil.which", Mock(return_value="/usr/bin/mysql"))
class MySqlProviderDropDatabaseTests(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_drop_database(self, check_mock):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        provider.drop_database()
        check_mock.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "root", "-ppassword", "--execute", "DROP DATABASE IF EXISTS `db_name`;"])


@patch("shutil.which", Mock(return_value="/usr/bin/mysql"))
class MySqlProviderConnectionTests(unittest.TestCase):
    @patch("subprocess.check_output", Mock(side_effect=CalledProcessError(1, "")) )
    def test_connection_fail(self):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        self.assertFalse(provider.test_connection())

    @patch("subprocess.check_output", Mock(return_value=b""))
    def test_connection_success(self):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        self.assertTrue( provider.test_connection() )