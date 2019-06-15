import pytest
import unittest
from unittest.mock import patch, Mock, mock_open
from pynonymizer.__main__ import main
from pynonymizer.pynonymize import ArgumentValidationError, DatabaseConnectionError, pynonymize
from types import SimpleNamespace

def test_pynonymize_missing_db_credentials():
    with pytest.raises(ArgumentValidationError):
        pynonymize(
            input_path="input.sql",
            strategyfile_path="strategyfile.yml",
            output_path="output.sql",
            db_user=None,
            db_password=None
        )


@patch("dotenv.find_dotenv")
@patch("dotenv.load_dotenv")
@patch("pynonymizer.__main__.create_parser")
@patch("pynonymizer.__main__.pynonymize", autospec=True)
def test_dotenv_called(pynonymize, create_parser, load_dotenv, find_dotenv):
    """
    dotenv should be called, and the parsed set of args should be passed to the pynonymize main function
    """
    parser_mock = Mock(parse_args=Mock(return_value=SimpleNamespace(
        legacy_input=None,
        legacy_strategyfile=None,
        legacy_output=None,
        input="TEST_INPUT",
        strategyfile="TEST_STRATEGYFILE",
        output="TEST_OUTPUT",
        db_type="TEST_TYPE",
        db_host="TEST_HOST",
        db_name="TEST_NAME",
        db_user="TEST_USER",
        db_password="TEST_PASSWORD",
        fake_locale="TEST_LOCALE",
        start_at_step="TEST_START_AT_STEP",
        skip_steps=["TEST_SKIP_1", "TEST_SKIP_2"],
        stop_at_step="TEST_STOP_AT_STEP"
    )))
    create_parser.return_value = parser_mock

    main(["input.sql", "strategyfile.yml", "output.sql"])

    find_dotenv.assert_called()
    load_dotenv.assert_called()
    create_parser.assert_called()
    parser_mock.parse_args.assert_called()

    pynonymize.assert_called_once_with(
        input_path="TEST_INPUT",
        strategyfile_path="TEST_STRATEGYFILE",
        output_path="TEST_OUTPUT",
        db_type="TEST_TYPE",
        db_host="TEST_HOST",
        db_name="TEST_NAME",
        db_user="TEST_USER",
        db_password="TEST_PASSWORD",
        fake_locale="TEST_LOCALE",
        start_at_step="TEST_START_AT_STEP",
        skip_steps=["TEST_SKIP_1","TEST_SKIP_2"],
        stop_at_step="TEST_STOP_AT_STEP"
    )


@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("pynonymizer.__main__.create_parser", Mock())
@patch("pynonymizer.__main__.pynonymize", Mock(side_effect=ArgumentValidationError(["test validation"])))
def test_sysexit_on_argument_invalid():
    """
    If pynonymize throws an argument validation error, main should exit with err 2
    """
    with pytest.raises(SystemExit) as e_info:
        main(["blah"])

    assert e_info.value.code == 2

@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("pynonymizer.__main__.create_parser", Mock())
@patch("pynonymizer.__main__.pynonymize", Mock(side_effect=DatabaseConnectionError()))
def test_sysexit_on_database_connection_error():
    """
    If pynonymize throws an argument validation error, main should exit with err 1
    """
    with pytest.raises(SystemExit) as e_info:
        main(["blah"])

    assert e_info.value.code == 1


@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("yaml.safe_load")
@patch("pynonymizer.pynonymize.get_provider")
@patch("pynonymizer.pynonymize.FakeColumnSet")
@patch("pynonymizer.pynonymize.StrategyParser")
@patch("pynonymizer.pynonymize.input.from_location")
@patch("pynonymizer.pynonymize.output.from_location")
@patch("builtins.open", mock_open(read_data="TESTFILEDATA"))
class MainProcessTests(unittest.TestCase):
    def test_pynonymize_main_process(self, output_from, input_from, StrategyParser, FakeColumnSet, get_provider, yaml_safe_load):
        """
        a rough smoke test for the main process. This needs an integration test to back it up.
        """
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE"
        )
        StrategyParser.return_value.parse_config.assert_called_with(yaml_safe_load.return_value)
        get_provider.assert_called_with("TEST_TYPE", "TEST_HOST", "TEST_USER", "TEST_PASSWORD", "TEST_NAME")

        provider = get_provider.return_value
        provider.test_connection.assert_called()
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()

    def test_pynonymize_stop_at_step(self, output_from, input_from, StrategyParser, FakeColumnSet, get_provider, yaml_safe_load):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            stop_at_step="ANONYMIZE_DB"
        )
        StrategyParser.return_value.parse_config.assert_called_with(yaml_safe_load.return_value)
        get_provider.assert_called_with("TEST_TYPE", "TEST_HOST", "TEST_USER", "TEST_PASSWORD", "TEST_NAME")

        provider = get_provider.return_value
        provider.test_connection.assert_called()
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_not_called()

    def test_pynonymize_skip_steps(self, output_from, input_from, StrategyParser, FakeColumnSet, get_provider,
                                     yaml_safe_load):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            skip_steps=["ANONYMIZE_DB", "CREATE_DB", "DUMP_DB"]
        )
        StrategyParser.return_value.parse_config.assert_called_with(yaml_safe_load.return_value)
        get_provider.assert_called_with("TEST_TYPE", "TEST_HOST", "TEST_USER", "TEST_PASSWORD", "TEST_NAME")

        provider = get_provider.return_value
        provider.test_connection.assert_called()
        provider.create_database.assert_not_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_not_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_called()


    def test_pynonymize_start_at_step(self, output_from, input_from, StrategyParser, FakeColumnSet, get_provider, yaml_safe_load):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="ANONYMIZE_DB"
        )
        StrategyParser.return_value.parse_config.assert_called_with(yaml_safe_load.return_value)
        get_provider.assert_called_with("TEST_TYPE", "TEST_HOST", "TEST_USER", "TEST_PASSWORD", "TEST_NAME")

        provider = get_provider.return_value
        provider.test_connection.assert_called()
        provider.create_database.assert_not_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()