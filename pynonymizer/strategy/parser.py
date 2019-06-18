from pynonymizer.strategy.exceptions import UnknownColumnStrategyError, UnknownTableStrategyError
from pynonymizer.log import get_logger
from pynonymizer.strategy.table import UpdateColumnsTableStrategy, TruncateTableStrategy, TableStrategyTypes
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes, EmptyUpdateColumnStrategy, UniqueEmailUpdateColumnStrategy, UniqueLoginUpdateColumnStrategy, FakeUpdateColumnStrategy
from pynonymizer.strategy.database import DatabaseStrategy
from enum import Enum

logger = get_logger(__name__)



class StrategyParser:
    def __init__(self, fake_seeder):
        self.fake_seeder = fake_seeder

    @staticmethod
    def __normalize_table_config(table_config):
        # If the table config doesn't have a "type" specified, it needs to be determined automatically.
        if "type" not in table_config:
            if "columns" in table_config:
                return {
                    "type": TableStrategyTypes.UPDATE_COLUMNS.value,
                    "columns": {
                        **table_config["columns"]
                    }
                }

            elif table_config == "truncate":
                return {
                    "type": TableStrategyTypes.TRUNCATE.value,
                }

            else:
                raise UnknownTableStrategyError(table_config)

        else:
            return table_config

    @staticmethod
    def __normalize_column_config(column_config):
        # If the column config doesn't have a "type" specified, it needs to be determined automatically.
        if "type" not in column_config:
            if column_config == "empty":
                return {
                    "type": UpdateColumnStrategyTypes.EMPTY.value
                }

            elif column_config == "unique_email":
                return {
                    "type": UpdateColumnStrategyTypes.UNIQUE_EMAIL.value
                }

            elif column_config == "unique_login":
                return {
                    "type": UpdateColumnStrategyTypes.UNIQUE_LOGIN.value
                }

            else:
                # Can't match it to anything special, must be a fake_update type. move the value to the fake_type field
                return {
                    "type": UpdateColumnStrategyTypes.FAKE_UPDATE.value,
                    "fake_type": column_config
                }
        else:
            return column_config

    def __parse_update_column(self, column_config):
        column_config = StrategyParser.__normalize_column_config(column_config)

        update_column_type = UpdateColumnStrategyTypes.from_value(column_config["type"])

        if update_column_type == UpdateColumnStrategyTypes.EMPTY:
            return EmptyUpdateColumnStrategy()

        elif update_column_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN:
            return UniqueLoginUpdateColumnStrategy()

        elif update_column_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL:
            return UniqueEmailUpdateColumnStrategy()

        elif update_column_type == UpdateColumnStrategyTypes.FAKE_UPDATE:
            return FakeUpdateColumnStrategy(self.fake_seeder, column_config["fake_type"])
        else:
            raise UnknownColumnStrategyError(column_config)

    def __parse_update_column_map(self,  column_map):

        parsed_columns = {}
        for name, column_config in column_map.items():
            parsed_columns[name] = self.__parse_update_column(column_config)

        return parsed_columns

    def __parse_table(self, table_config):
        table_config = StrategyParser.__normalize_table_config(table_config)

        table_strategy = TableStrategyTypes.from_value(table_config["type"])

        if table_strategy == TableStrategyTypes.TRUNCATE:
            return TruncateTableStrategy()
        elif table_strategy == TableStrategyTypes.UPDATE_COLUMNS:
            raw_column_map = table_config["columns"]
            column_strategy_map = self.__parse_update_column_map(raw_column_map)
            return UpdateColumnsTableStrategy(column_strategy_map)
        else:
            raise UnknownTableStrategyError(table_config)

    def parse_config(self, config):
        table_strategies = {}
        for table_name, table_config in config["tables"].items():
            table_strategies[table_name] = self.__parse_table(table_config)

        scripts = {}
        try:
            scripts = config["scripts"]
        except KeyError:
            pass

        return DatabaseStrategy(table_strategies, scripts)
