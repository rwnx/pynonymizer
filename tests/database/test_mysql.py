import unittest
from unittest.mock import Mock, patch, MagicMock, call

from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.database.exceptions import MissingPrerequisiteError, DatabaseConnectionError
from pynonymizer.fake import FakeColumn
import datetime

from subprocess import CalledProcessError

class MysqlProviderTest(unittest.TestCase):
    """
    These tests are fragile and rely on the actual SQL the provider is going to run.
    for more robustness, it might be more prudent to rely on some kind of sql-matching so minor changes like whitespace don't break all the tests!

    """
    @patch("shutil.which", Mock(return_value="/usr/bin/executable"))
    @patch("subprocess.check_output", Mock(return_value=b"mock output"))
    def test_attrs(self):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        assert provider.db_host == "1.2.3.4"
        assert provider.db_user == "root"
        assert provider.db_pass == "password"
        assert provider.db_name == "db_name"

    @patch("shutil.which", Mock(return_value=None))
    @patch("subprocess.check_output")
    def test_raise_on_missing_binaries(self, *_):
        with self.assertRaises(MissingPrerequisiteError):
            provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")

    @patch("shutil.which", Mock(return_value="/usr/bin/executable"))
    @patch("subprocess.check_output", Mock(side_effect=CalledProcessError(1, "test")))
    def test_raise_subprocess_error_database_connection(self):
        with self.assertRaises(DatabaseConnectionError):
            provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")

    @patch("shutil.which", Mock(return_value="/usr/bin/executable") )
    @patch("subprocess.check_output")
    def test_create_database(self, check_mock):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        provider.create_database()
        check_mock.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "root", "-ppassword", "--execute", "CREATE DATABASE `db_name`;"])


    @patch("subprocess.check_output")
    def test_drop_database(self, check_mock):
        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
        provider.drop_database()
        check_mock.assert_called_with(["mysql", "-h", "1.2.3.4", "-u", "root", "-ppassword", "--execute", "DROP DATABASE IF EXISTS `db_name`;"])

    @patch("shutil.which", Mock(return_value="/usr/bin/executable"))
    @patch("subprocess.check_output")
    def test_anonymize(self, check_mock):
        date = datetime.datetime(2019, 1,1)
        test_column1 = FakeColumn(Mock(), "test_column1", "VARCHAR(10)", lambda: "hello")
        test_column2 = FakeColumn(Mock(), "test_column2", "INT",         lambda: "456")
        test_column3 = FakeColumn(Mock(), "test_column3", "DATETIME", lambda: date)

        database_strategy = MagicMock(get_fake_columns=Mock(return_value=[test_column1, test_column2, test_column3]))

        provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")

        provider.anonymize_database(database_strategy)
        #check_mock.assert_called_with(['mysql', '-h', '1.2.3.4', '-u', 'root', '-ppassword', 'db_name', '--execute', 'CREATE TABLE `_pynonymizer_seed_fake_data` (`test_column1` VARCHAR(10),`test_column2` INT,`test_column3` DATETIME);'])
        #check_mock.assert_called_with(['mysql', '-h', '1.2.3.4', '-u', 'root', '-ppassword', 'db_name', '--execute', "INSERT INTO `_pynonymizer_seed_fake_data`(`test_column1`,`test_column2`,`test_column3`) VALUES ('hello','456','2019-01-01 00:00:00');"])
        #check_mock.assert_called_with(['mysql', '-h', '1.2.3.4', '-u', 'root', '-ppassword', 'db_name', '--execute', 'DROP TABLE IF EXISTS `_pynonymizer_seed_fake_data`;'])

