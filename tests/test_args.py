from unittest.mock import patch, Mock
from pynonymizer.__main__ import create_parser
import pytest


def test_legacy_positional_args():
    """
    When called with the positional args, argparse should return a working namespace with the correct values set
    :return:
    """
    args = create_parser().parse_args(["input.sql", "strategyfile.yml", "output.sql"])
    assert args.legacy_input == "input.sql"
    assert args.legacy_strategyfile == "strategyfile.yml"
    assert args.legacy_output == "output.sql"


def mock_getenv_old(name):
    """
    a mock for getenv to return the OLD environment variable set with pre-defined values
    """
    if name == "DB_TYPE":
        return "OLDENV_DB_TYPE"
    elif name == "DB_HOST":
        return "OLDENV_DB_HOST"
    elif name == "DB_NAME":
        return "OLDENV_DB_NAME"
    elif name == "DB_USER":
        return "OLDENV_DB_USER"
    elif name == "DB_PASS":
        return "OLDENV_DB_PASSWORD"
    elif name == "FAKE_LOCALE":
        return "OLDENV_FAKE_LOCALE"


def mock_getenv_none():
    """
    Simulates an empty envrionment variable set
    """
    return None


def mock_getenv_new(name):
    """
    a mock for getenv to return the NEW environment variable set with pre-defined values
    """
    if name == "PYNONYMIZER_DB_TYPE":
        return "ENV_DB_TYPE"
    elif name == "PYNONYMIZER_DB_HOST":
        return "ENV_DB_HOST"
    elif name == "PYNONYMIZER_DB_NAME":
        return "ENV_DB_NAME"
    elif name == "PYNONYMIZER_DB_USER":
        return "ENV_DB_USER"
    elif name == "PYNONYMIZER_DB_PASSWORD":
        return "ENV_DB_PASSWORD"
    elif name == "PYNONYMIZER_FAKE_LOCALE":
        return "ENV_FAKE_LOCALE"
    elif name == "PYNONYMIZER_INPUT":
        return "ENV_INPUT"
    elif name == "PYNONYMIZER_STRATEGY":
        return "ENV_STRATEGY"
    elif name == "PYNONYMIZER_OUTPUT":
        return "ENV_OUTPUT"
    elif name == "PYNONYMIZER_START_AT":
        return "ANONYMIZE_DB"
    elif name == "PYNONYMIZER_SKIP_STEPS":
        return "ANONYMIZE_DB DUMP_DB"
    elif name == "PYNONYMIZER_STOP_AT":
        return "ANONYMIZE_DB"


def mock_getenv_old_new_combined(name):
    """
    combine the outputs from the two mocking function sets
    """
    return mock_getenv_new(name) or mock_getenv_old(name)


@patch("os.getenv", Mock(side_effect=mock_getenv_old))
def test_old_environmental_defaults():
    """
    When not specified, arguments should fall back to OLD env vars (if specified)
    :return:
    """
    # Use positionals, since the old vars dont cover these
    args = create_parser().parse_args(["input.sql", "strategyfile.yml", "output.sql"])
    assert args.legacy_input        == "input.sql"
    assert args.legacy_strategyfile == "strategyfile.yml"
    assert args.legacy_output       == "output.sql"
    assert args.db_type      == "OLDENV_DB_TYPE"
    assert args.db_name      == "OLDENV_DB_NAME"
    assert args.db_host      == "OLDENV_DB_HOST"
    assert args.db_user      == "OLDENV_DB_USER"
    assert args.db_password  == "OLDENV_DB_PASSWORD"
    assert args.fake_locale  == "OLDENV_FAKE_LOCALE"


@patch("os.getenv", Mock(side_effect=mock_getenv_old_new_combined))
def test_environmental_defaults():
    """
    When not specified, arguments should fall back to NEW environmental defaults (PYNONYMIZER_*)
    old envs should take the lowest precedence and be ignored
    :return:
    """
    args = create_parser().parse_args([])
    assert args.input         == "ENV_INPUT"
    assert args.strategyfile  == "ENV_STRATEGY"
    assert args.output        == "ENV_OUTPUT"
    assert args.db_type       == "ENV_DB_TYPE"
    assert args.db_name       == "ENV_DB_NAME"
    assert args.db_host       == "ENV_DB_HOST"
    assert args.db_user       == "ENV_DB_USER"
    assert args.db_password   == "ENV_DB_PASSWORD"
    assert args.fake_locale   == "ENV_FAKE_LOCALE"
    assert args.start_at_step == "ANONYMIZE_DB"
    assert args.skip_steps    == ["ANONYMIZE_DB", "DUMP_DB"]
    assert args.stop_at_step  == "ANONYMIZE_DB"


@patch("os.getenv", Mock(side_effect=mock_getenv_new))
def test_all_legacy_new_mutex():
    """
    legacy posisitonals and new options should result in an error if specified together
    """
    with pytest.raises(SystemExit) as e_info:
        create_parser().parse_args(["input.sql", "strategyfile.yml", "output.sql",  "--input", "input2.sql"])

    with pytest.raises(SystemExit) as e_info:
        create_parser().parse_args(["input.sql", "strategyfile.yml", "output.sql",  "--strategy", "strategyfile2.yml"])

    with pytest.raises(SystemExit) as e_info:
        create_parser().parse_args(["input.sql", "strategyfile.yml", "output.sql",  "--output", "output2.sql"])


@patch("os.getenv", Mock(side_effect=mock_getenv_new))
def test_all_args_precedence():
    """
    All arguments should be overridden by their argv counterparts
    :return:
    """
    args = create_parser().parse_args([
        "--input",  "input.sql",
        "--strategy",  "strategyfile.yml",
        "--output", "output.sql",
        "--db-type", "ARG_DB_TYPE",
        "--db-host", "ARG_DB_HOST",
        "--db-name", "ARG_DB_NAME",
        "--db-user", "ARG_DB_USER",
        "--db-password", "ARG_DB_PASSWORD",
        "--fake-locale", "ARG_FAKE_LOCALE",
        "--start-at", "START",
        "--skip-steps", "ANONYMIZE_DB",
        "--stop-at", "END"
    ])
    assert args.input          == "input.sql"
    assert args.strategyfile   == "strategyfile.yml"
    assert args.output         == "output.sql"
    assert args.db_type        == "ARG_DB_TYPE"
    assert args.db_name        == "ARG_DB_NAME"
    assert args.db_host        == "ARG_DB_HOST"
    assert args.db_user        == "ARG_DB_USER"
    assert args.db_password    == "ARG_DB_PASSWORD"
    assert args.fake_locale    == "ARG_FAKE_LOCALE"
    assert args.start_at_step  == "START"
    assert args.skip_steps     == ["ANONYMIZE_DB"]
    assert args.stop_at_step   == "END"


@patch("os.getenv", Mock(side_effect=mock_getenv_new))
def test_all_short_args_precedence():
    """
    All arguments should be overridden by their argv counterparts (using short options!)
    :return:
    """
    args = create_parser().parse_args([
        "-i", "input.sql",
        "-s", "strategyfile.yml",
        "-o", "output.sql",
        "-t", "ARG_DB_TYPE",
        "-d", "ARG_DB_HOST",
        "-n", "ARG_DB_NAME",
        "-u", "ARG_DB_USER",
        "-p", "ARG_DB_PASSWORD",
        "-l", "ARG_FAKE_LOCALE"
    ])
    assert args.input        == "input.sql"
    assert args.strategyfile == "strategyfile.yml"
    assert args.output       == "output.sql"
    assert args.db_type      == "ARG_DB_TYPE"
    assert args.db_name      == "ARG_DB_NAME"
    assert args.db_host      == "ARG_DB_HOST"
    assert args.db_user      == "ARG_DB_USER"
    assert args.db_password  == "ARG_DB_PASSWORD"
    assert args.fake_locale  == "ARG_FAKE_LOCALE"
