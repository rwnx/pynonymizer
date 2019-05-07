from unittest.mock import patch
from pynonymizer.__main__ import create_parser

def test_valid_args():
    args = create_parser().parse_args(["input.sql", "strategyfile.yml", "output.sql", "--db-name", "database_name"])
    assert args.input == "input.sql"
    assert args.strategyfile == "strategyfile.yml"
    assert args.output == "output.sql"
    assert args.db_name == "database_name"

# patch stderr to remove usage echo into test output
@patch("sys.exit")
@patch('sys.stderr')
def test_no_args(stderr_mock, exit_mock):
    args = create_parser().parse_args([])

    exit_mock.assert_called_once_with(2)
    stderr_mock.write.assert_called()


@patch("sys.exit")
@patch('sys.stderr')
def test_missing_positional(stderr_mock, exit_mock):
    args = create_parser().parse_args(["input.sql", "strategyfile.yml"])

    exit_mock.assert_called_once_with(2)
    stderr_mock.write.assert_called()

