import unittest
from unittest.mock import Mock, patch, MagicMock, call

from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.database.exceptions import MissingPrerequisiteError
from pynonymizer.fake import FakeColumn
import datetime

from subprocess import CalledProcessError

class MySqlProviderInitTest(unittest.TestCase):
    @patch("shutil.which", Mock(return_value=None))
    @patch("subprocess.check_output", Mock())
    def test_raise_on_missing_binaries(self):
        """
        When shutil.which returns no binary path, provider should throw MissingPrerequisiteError
        """
        with self.assertRaises(MissingPrerequisiteError):
            provider = MySqlProvider("1.2.3.4", "root", "password", "db_name")
