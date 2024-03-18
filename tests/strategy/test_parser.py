from pynonymizer.fake import (
    UnsupportedFakeArgumentsError,
    UnsupportedFakeTypeError,
    FakeColumnGenerator,
)
from pynonymizer.strategy import database
from pynonymizer.strategy.exceptions import (
    UnknownTableStrategyError,
    UnknownColumnStrategyError,
    ConfigSyntaxError,
)
from pynonymizer.strategy.table import TableStrategyTypes
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes
import copy
import pytest
import yaml
import os.path


def local_yaml(name: str) -> str:
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    with open(filepath) as file:
        return yaml.safe_load(file.read())


@pytest.fixture
def smoke_test() -> dict:
    return local_yaml("smoke_test.yml")


@pytest.fixture
def invalid_unsupported_fake_type():
    return local_yaml("invalid_unsupported_fake_type.yml")


@pytest.fixture
def invalid_unsupported_fake_args():
    return local_yaml("invalid_unsupported_fake_args.yml")


@pytest.fixture
def invalid_unsupported_table_type():
    return local_yaml("invalid_unsupported_table_type.yml")


@pytest.fixture
def invalid_unsupported_column_type():
    return local_yaml("invalid_unsupported_column_type.yml")


@pytest.fixture
def invalid_custom_provider_unknown_module():
    return local_yaml("invalid_custom_provider_unknown_module.yml")


@pytest.fixture
def strategy_parser():
    from pynonymizer.strategy import parser

    return parser.StrategyParser()


def test_valid_parse_no_mutate(smoke_test, strategy_parser):
    deep_copy = copy.deepcopy(smoke_test)
    strategy_parser.parse_config(smoke_test)

    assert smoke_test == deep_copy


def test_custom_provider_missing_import_should_raise_error(
    strategy_parser, invalid_custom_provider_unknown_module
):
    with pytest.raises(Exception):
        strategy_parser.parse_config(invalid_custom_provider_unknown_module)


def test_smoke_test__should_contain_truncate_table(strategy_parser, smoke_test):
    strategy = strategy_parser.parse_config(smoke_test)

    truncate = next(
        x for x in strategy.table_strategies if x.table_name == "truncate_table"
    )

    assert truncate.strategy_type == TableStrategyTypes.TRUNCATE


def test_smoke_test__should_contain_delete_table(strategy_parser, smoke_test):
    strategy = strategy_parser.parse_config(smoke_test)

    delete = next(
        x for x in strategy.table_strategies if x.table_name == "delete_table"
    )

    assert delete.strategy_type == TableStrategyTypes.DELETE


def test_smoke_test__should_contain_update_column_table(strategy_parser, smoke_test):
    strategy = strategy_parser.parse_config(smoke_test)
    update_columns = next(
        x for x in strategy.table_strategies if x.table_name == "update_column_table"
    )

    assert update_columns.strategy_type == TableStrategyTypes.UPDATE_COLUMNS


def test_smoke_test__should_contain_scripts(strategy_parser, smoke_test):
    strategy = strategy_parser.parse_config(smoke_test)

    assert len(strategy.before_scripts) > 0
    assert len(strategy.after_scripts) > 0


def test_smoke_test__update_columns_should_parse_verbose_and_shorthand_identical(
    strategy_parser, smoke_test
):
    strategy = strategy_parser.parse_config(smoke_test)

    update_columns = next(
        x for x in strategy.table_strategies if x.table_name == "update_column_table"
    )

    unique_login = next(
        x for x in update_columns.column_strategies if x.column_name == "unique_login"
    )
    unique_login_verbose = next(
        x
        for x in update_columns.column_strategies
        if x.column_name == "unique_login_verbose"
    )

    unique_email = next(
        x for x in update_columns.column_strategies if x.column_name == "unique_email"
    )
    unique_email_verbose = next(
        x
        for x in update_columns.column_strategies
        if x.column_name == "unique_email_verbose"
    )

    fake_update_shorthand = next(
        x
        for x in update_columns.column_strategies
        if x.column_name == "fake_update_shorthand"
    )
    fake_update_verbose = next(
        x
        for x in update_columns.column_strategies
        if x.column_name == "fake_update_verbose"
    )

    literal_column_shorthand = next(
        x
        for x in update_columns.column_strategies
        if x.column_name == "literal_column_shorthand"
    )
    literal_column_verbose = next(
        x
        for x in update_columns.column_strategies
        if x.column_name == "literal_column_verbose"
    )

    assert unique_login.strategy_type == unique_login_verbose.strategy_type

    assert unique_email.strategy_type == unique_email_verbose.strategy_type

    assert fake_update_shorthand.strategy_type == fake_update_verbose.strategy_type
    assert fake_update_shorthand.fake_type == fake_update_verbose.fake_type

    assert (
        literal_column_shorthand.strategy_type == literal_column_verbose.strategy_type
    )
    assert literal_column_shorthand.value == literal_column_verbose.value


def test_unsupported_fake_column_type__should_raise_unsupported_fake_type(
    strategy_parser, invalid_unsupported_fake_type
):
    with pytest.raises(UnsupportedFakeTypeError):
        strategy_parser.parse_config(invalid_unsupported_fake_type)


def test_unsupported_fake_column_type__should_raise_unsupported_fake_args(
    strategy_parser, invalid_unsupported_fake_args
):
    with pytest.raises(UnsupportedFakeArgumentsError):
        strategy_parser.parse_config(invalid_unsupported_fake_args)


def test_unsupported_fake_column_type__should_raise_unsupported_fake_args(
    strategy_parser, invalid_unsupported_table_type
):
    with pytest.raises(UnknownTableStrategyError):
        strategy_parser.parse_config(invalid_unsupported_table_type)


def test_unsupported_fake_column_type__should_raise_unsupported_fake_args(
    strategy_parser, invalid_unsupported_column_type
):
    with pytest.raises(UnknownColumnStrategyError):
        strategy_parser.parse_config(invalid_unsupported_column_type)
