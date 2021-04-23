import pytest
import unittest
from unittest.mock import patch, Mock, mock_open
from pynonymizer.cli import cli
from pynonymizer.pynonymize import ArgumentValidationError, DatabaseConnectionError
from types import SimpleNamespace


def mock_getenv_old(name):
    if name.startswith("PYNONYMIZER_"):
        return None
    return f"OLDENV_{name}"

@patch("dotenv.find_dotenv")
@patch("dotenv.load_dotenv")
@patch("pynonymizer.cli.create_parser")
@patch("pynonymizer.cli.pynonymize", autospec=True)
class MainArgTests(unittest.TestCase):
    def setUp(self):
        self.parsed_args = SimpleNamespace(
            legacy_input=None,
            legacy_strategyfile=None,
            legacy_output=None,
            input="TEST_INPUT",
            strategyfile="TEST_STRATEGYFILE",
            output="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="TEST_START_AT_STEP",
            skip_steps=["TEST_SKIP_1", "TEST_SKIP_2"],
            stop_at_step="TEST_STOP_AT_STEP",
            only_step="TEST_ONLY_STEP",
            seed_rows=None,
            mssql_driver=None,
            mssql_backup_compression=False,
            mysql_dump_opts="--additional",
            mysql_cmd_opts="--additional",
            postgres_dump_opts="--additional",
            postgres_cmd_opts="--additional",
            dry_run=True,
            verbose=True
        )
    @patch("os.getenv", Mock(side_effect=mock_getenv_old))
    def test_when_old_env_should_call_pynonymizer(self, pynonymize, create_parser, load_dotenv, find_dotenv):
        parser_mock = Mock(parse_args=Mock(return_value=self.parsed_args))
        create_parser.return_value = parser_mock

        cli([])
        pynonymize.assert_called_once_with(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="TEST_START_AT_STEP",
            skip_steps=["TEST_SKIP_1", "TEST_SKIP_2"],
            stop_at_step="TEST_STOP_AT_STEP",
            only_step="TEST_ONLY_STEP",
            seed_rows=None,
            mssql_driver=None,
            mssql_backup_compression=False,
            mysql_dump_opts="--additional",
            mysql_cmd_opts="--additional",
            postgres_dump_opts="--additional",
            postgres_cmd_opts="--additional",
            dry_run=True,
            verbose=True
        )

    def test_dotenv_called(self, pynonymize, create_parser, load_dotenv, find_dotenv):
        """
        dotenv should be called
        """
        parser_mock = Mock(parse_args=Mock(return_value=self.parsed_args))
        create_parser.return_value = parser_mock

        cli([])

        find_dotenv.assert_called()
        load_dotenv.assert_called()

    def test_arg_pass_legacy_override(self, pynonymize, create_parser, load_dotenv, find_dotenv):
        """
        the parsed set of args should be passed to the pynonymize cli function
        legacy args should override normal ones to account for old positional behaviour
        """
        self.parsed_args.legacy_input = "LEGACY_INPUT"
        self.parsed_args.legacy_strategyfile = "LEGACY_STRATEGYFILE"
        self.parsed_args.legacy_output = "LEGACY_OUTPUT"
        parser_mock = Mock(parse_args=Mock(return_value=self.parsed_args))
        create_parser.return_value = parser_mock

        cli([])

        create_parser.assert_called()
        parser_mock.parse_args.assert_called()

        call_kwargs = pynonymize.call_args[1]

        assert call_kwargs["input_path"] == "LEGACY_INPUT"
        assert call_kwargs["strategyfile_path"] == "LEGACY_STRATEGYFILE"
        assert call_kwargs["output_path"]       == "LEGACY_OUTPUT"


    def test_arg_pass_normal(self, pynonymize, create_parser, load_dotenv, find_dotenv):
        """
        the parsed set of args should be passed to the pynonymize cli function
        """
        parser_mock = Mock(parse_args=Mock(return_value=self.parsed_args))
        create_parser.return_value = parser_mock

        cli([])

        create_parser.assert_called()
        parser_mock.parse_args.assert_called()
        pynonymize.assert_called_once_with(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="TEST_START_AT_STEP",
            skip_steps=["TEST_SKIP_1", "TEST_SKIP_2"],
            stop_at_step="TEST_STOP_AT_STEP",
            only_step="TEST_ONLY_STEP",
            seed_rows=None,
            mssql_driver=None,
            mssql_backup_compression=False,
            mysql_dump_opts="--additional",
            mysql_cmd_opts="--additional",
            postgres_dump_opts="--additional",
            postgres_cmd_opts="--additional",
            dry_run=True,
            verbose=True
        )


@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("pynonymizer.cli.create_parser", Mock())
@patch("pynonymizer.cli.pynonymize", Mock(side_effect=ArgumentValidationError(["test validation"])))
def test_sysexit_on_argument_invalid():
    """
    If pynonymize throws an argument validation error, cli should exit with err 2
    """
    with pytest.raises(SystemExit) as e_info:
        cli(["blah"])

    assert e_info.value.code == 2

@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("pynonymizer.cli.create_parser", Mock())
@patch("pynonymizer.cli.pynonymize", Mock(side_effect=DatabaseConnectionError()))
def test_sysexit_on_database_connection_error():
    """
    If pynonymize throws an argument validation error, cli should exit with err 1
    """
    with pytest.raises(SystemExit) as e_info:
        cli(["blah"])

    assert e_info.value.code == 1