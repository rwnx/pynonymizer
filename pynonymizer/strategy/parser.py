from pynonymizer.fake import FakeColumnGenerator
from pynonymizer.strategy.exceptions import (
    UnknownColumnStrategyError,
    UnknownTableStrategyError,
    ConfigSyntaxError,
)
from pynonymizer.strategy.table import (
    UpdateColumnsTableStrategy,
    TruncateTableStrategy,
    DeleteTableStrategy,
    TableStrategyTypes,
)
from pynonymizer.strategy.update_column import (
    UpdateColumnStrategyTypes,
    EmptyUpdateColumnStrategy,
    UniqueEmailUpdateColumnStrategy,
    UniqueLoginUpdateColumnStrategy,
    FakeUpdateColumnStrategy,
    LiteralUpdateColumnStrategy,
)
from pynonymizer.strategy.database import DatabaseStrategy
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class StrategyParser:
    def __init__(self):
        pass

    @staticmethod
    def __normalize_table_config(table_config):
        # If the table config doesn't have a "type" specified, it needs to be determined automatically.
        if "type" not in table_config:
            if "columns" in table_config:
                return {
                    **table_config,
                    "type": TableStrategyTypes.UPDATE_COLUMNS.value,
                }

            elif table_config == "truncate":
                return {
                    "type": TableStrategyTypes.TRUNCATE.value,
                }

            elif table_config == "delete":
                return {
                    "type": TableStrategyTypes.DELETE.value,
                }

            else:
                raise UnknownTableStrategyError(table_config)

        else:
            return table_config

    @staticmethod
    def __normalize_column_config(column_config):
        if isinstance(column_config, dict) and "type" in column_config:
            return column_config

        # If the column config is not a dict with "type" specified, the type needs to be determined automatically.
        else:
            if column_config == "empty":
                return {"type": UpdateColumnStrategyTypes.EMPTY.value}

            elif column_config == "unique_email":
                return {"type": UpdateColumnStrategyTypes.UNIQUE_EMAIL.value}

            elif column_config == "unique_login":
                return {"type": UpdateColumnStrategyTypes.UNIQUE_LOGIN.value}
            elif column_config.startswith("(") and column_config.endswith(")"):
                return {
                    "type": UpdateColumnStrategyTypes.LITERAL.value,
                    "value": column_config,
                }

            else:
                # Can't match it to anything special, must be a fake_update type. move the value to the fake_type field
                return {
                    "type": UpdateColumnStrategyTypes.FAKE_UPDATE.value,
                    "fake_type": column_config,
                }

    @staticmethod
    def __normalize_table_list(config):
        # if tables is given in dict form, normalize to list with table_name key
        if "tables" in config and isinstance(config["tables"], dict):
            tables_list = []
            for table_name, table_config in config["tables"].items():
                normalized_table = StrategyParser.__normalize_table_config(table_config)
                normalized_table["table_name"] = table_name
                tables_list.append(normalized_table)

            config["tables"] = tables_list

        return config

    @staticmethod
    def __normalize_update_columns_list(columns_config):
        # if columns is given in dict form, normalize to list
        if isinstance(columns_config, dict):
            column_list = []
            for column_name, column_config in columns_config.items():
                normalized_column = StrategyParser.__normalize_column_config(
                    column_config
                )
                normalized_column["column_name"] = column_name
                column_list.append(normalized_column)

            return column_list

        elif isinstance(columns_config, list):
            return [
                StrategyParser.__normalize_column_config(col) for col in columns_config
            ]
        else:
            raise ConfigSyntaxError(
                "Unknown update column config syntax: {}".format(columns_config)
            )

    def __parse_update_column(self, column_config):
        update_column_type = UpdateColumnStrategyTypes.from_value(
            column_config.pop("type")
        )
        try:
            if update_column_type == UpdateColumnStrategyTypes.EMPTY:
                logger.warning(
                    "DeprecationWarning: UpdateColumnStrategyTypes.EMPTY is deprecated and may be removed in a future release."
                )
                return EmptyUpdateColumnStrategy(**column_config)

            elif update_column_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN:
                return UniqueLoginUpdateColumnStrategy(**column_config)

            elif update_column_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL:
                return UniqueEmailUpdateColumnStrategy(**column_config)

            elif update_column_type == UpdateColumnStrategyTypes.FAKE_UPDATE:
                return FakeUpdateColumnStrategy(
                    fake_column_generator=self.fake_seeder, **column_config
                )

            elif update_column_type == UpdateColumnStrategyTypes.LITERAL:
                return LiteralUpdateColumnStrategy(**column_config)

            else:
                raise UnknownColumnStrategyError(column_config)
        except TypeError as error:
            # TypeError can be thrown when the dict args dont match the constructors for the types. We need to re-throw
            raise ConfigSyntaxError()

    def __parse_table(self, table_config):
        table_strategy = TableStrategyTypes.from_value(table_config.pop("type"))

        try:
            if table_strategy == TableStrategyTypes.TRUNCATE:
                return TruncateTableStrategy(**table_config)
            elif table_strategy == TableStrategyTypes.DELETE:
                return DeleteTableStrategy(**table_config)
            elif table_strategy == TableStrategyTypes.UPDATE_COLUMNS:
                # update columns supports dict and list columns, so this has to be normalized again during parsing.
                normalized_columns = StrategyParser.__normalize_update_columns_list(
                    table_config.pop("columns")
                )
                parsed_columns = [
                    self.__parse_update_column(column) for column in normalized_columns
                ]

                return UpdateColumnsTableStrategy(
                    column_strategies=parsed_columns, **table_config
                )
            else:
                raise UnknownTableStrategyError(table_config)

        except TypeError as error:
            # TypeError can be thrown when the dict args dont match the constructors for the types. We need to re-throw
            raise ConfigSyntaxError()

    def parse_config(self, raw_config, locale_override=None):
        """
        parse a configuration dict into a DatabaseStrategy.
        :param raw_config:
        :return:
        """
        config = StrategyParser.__normalize_table_list(deepcopy(raw_config))

        locale = config.get("locale", "en_GB")
        if locale_override:
            locale = locale_override

        providers = config.get("providers", [])
        self.fake_seeder = FakeColumnGenerator(locale=locale, providers=providers)

        table_strategies = [
            self.__parse_table(table_config) for table_config in config["tables"]
        ]

        before_scripts = None
        after_scripts = None
        try:
            scripts = config["scripts"]

            if "before" in scripts:
                before_scripts = scripts["before"]

            if "after" in scripts:
                after_scripts = scripts["after"]
        except KeyError:
            pass

        return DatabaseStrategy(
            table_strategies=table_strategies,
            before_scripts=before_scripts,
            after_scripts=after_scripts,
        )
