from unittest.mock import patch, Mock
from pynonymizer.cli import create_parser
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
    if name.startswith("PYNONYMIZER_"):
        return None
    return f"OLDENV_{name}"


def mock_getenv_none():
    """
    Simulates an empty envrionment variable set
    """
    return None


def mock_getenv_new(name):
    if name=="PYNONYMIZER_SEED_ROWS":
        return "50"
    else:
        return f"ENV_{name}"


def mock_getenv_old_new_combined(name):
    return mock_getenv_new(name) or mock_getenv_old(name)


@patch("os.getenv", Mock(side_effect=mock_getenv_old))
def test_when_old_env_is_passed__should_use_old_environmental_vars():
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
    assert args.db_password  == "OLDENV_DB_PASS"
    assert args.fake_locale  == "OLDENV_FAKE_LOCALE"


@patch("os.getenv", Mock(side_effect=mock_getenv_old_new_combined))
def test_when_old_and_new_env_is_specified__should_use_new_environmental_vars():
    """
    When not specified, arguments should fall back to NEW environmental defaults (PYNONYMIZER_*)
    old envs should take the lowest precedence and be ignored
    :return:
    """
    args = create_parser().parse_args([])
    assert args.input         == "ENV_PYNONYMIZER_INPUT"
    assert args.strategyfile  == "ENV_PYNONYMIZER_STRATEGY"
    assert args.output        == "ENV_PYNONYMIZER_OUTPUT"
    assert args.db_type       == "ENV_PYNONYMIZER_DB_TYPE"
    assert args.db_name       == "ENV_PYNONYMIZER_DB_NAME"
    assert args.db_host       == "ENV_PYNONYMIZER_DB_HOST"
    assert args.db_user       == "ENV_PYNONYMIZER_DB_USER"
    assert args.db_password   == "ENV_PYNONYMIZER_DB_PASSWORD"
    assert args.fake_locale   == "ENV_PYNONYMIZER_FAKE_LOCALE"
    assert args.seed_rows   == 50
    assert args.start_at_step == "ENV_PYNONYMIZER_START_AT"
    assert args.skip_steps    == ["ENV_PYNONYMIZER_SKIP_STEPS"]
    assert args.stop_at_step  == "ENV_PYNONYMIZER_STOP_AT"

    # Not a fair test because store_true ?
    assert args.mssql_backup_compression  == True
    assert args.mysql_cmd_opts  == "ENV_PYNONYMIZER_MYSQL_CMD_OPTS"
    assert args.mysql_dump_opts  == "ENV_PYNONYMIZER_MYSQL_DUMP_OPTS"
    assert args.postgres_cmd_opts  == "ENV_PYNONYMIZER_POSTGRES_CMD_OPTS"
    assert args.postgres_dump_opts  == "ENV_PYNONYMIZER_POSTGRES_DUMP_OPTS"


@patch("os.getenv", Mock(side_effect=mock_getenv_new))
def test_positions_and_options_should_be_mutally_exclusive():
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
def test_when_long_args_are_specified_and_new_env__should_use_args_first():
    """
    All ENV should be overridden by their argv counterparts
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
        "--seed-rows", "2341",
        "--fake-locale", "ARG_FAKE_LOCALE",
        "--start-at", "START",
        "--skip-steps", "ANONYMIZE_DB",
        "--stop-at", "END",
        "--verbose",
        "--mssql-backup-compression",
        "--mysql-cmd-opts=\"ARG_MYSQL_CMD_OPTS\"",
        "--mysql-dump-opts=\"ARG_MYSQL_DUMP_OPTS\"",
        "--postgres-cmd-opts=\"ARG_POSTGRES_CMD_OPTS\"",
        "--postgres-dump-opts=\"ARG_POSTGRES_DUMP_OPTS\"",


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
    assert args.verbose is True
    assert args.seed_rows == 2341

    assert args.mssql_backup_compression is True
    assert args.mysql_cmd_opts      == "\"ARG_MYSQL_CMD_OPTS\""
    assert args.mysql_dump_opts     == "\"ARG_MYSQL_DUMP_OPTS\""
    assert args.postgres_cmd_opts   == "\"ARG_POSTGRES_CMD_OPTS\""
    assert args.postgres_dump_opts  == "\"ARG_POSTGRES_DUMP_OPTS\""


@patch("os.getenv", Mock(side_effect=mock_getenv_new))
def test_when_short_args_are_specified_and_new_env__should_use_args_first():
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
