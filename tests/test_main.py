import pytest
from unittest.mock import patch, Mock
from pynonymizer.__main__ import ArgumentValidationError, pynonymize, main
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
        input="TEST_INPUT",
        strategyfile="TEST_STRATEGYFILE",
        output="TEST_OUTPUT",
        db_type="TEST_TYPE",
        db_host="TEST_HOST",
        db_name="TEST_NAME",
        db_user="TEST_USER",
        db_password="TEST_PASSWORD",
        fake_locale="TEST_LOCALE"
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
        fake_locale="TEST_LOCALE"
    )


@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("pynonymizer.__main__.create_parser", Mock())
@patch("pynonymizer.__main__.pynonymize", Mock(side_effect=ArgumentValidationError(["test validation"])))
def test_sysexit_on_argument_invalid():
    """
    If pynonymize throws an argument validation error, main should exit with err 1
    """
    with pytest.raises(SystemExit) as e_info:
        main(["blah"])

    assert e_info.value.code == 2