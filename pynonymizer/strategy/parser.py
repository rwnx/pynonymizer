from pynonymizer.strategy.exceptions import UnknownColumnStrategyError, UnknownTableStrategyError
from pynonymizer.log import get_logger
from pynonymizer.strategy.table import UpdateColumnsTableStrategy, TruncateTableStrategy
from pynonymizer.strategy.update_column import EmptyUpdateColumnStrategy, UniqueEmailUpdateColumnStrategy, UniqueLoginUpdateColumnStrategy, FakeUpdateColumnStrategy
from pynonymizer.strategy.database import DatabaseStrategy

logger = get_logger(__name__)


class StrategyParser:
    def __init__(self, fake_seeder):
        self.fake_seeder = fake_seeder

    def __parse_update_column(self, column_name, column_config):
        # autodetect shorthand
        if isinstance(column_config, str):
            if column_config == "empty":
                return EmptyUpdateColumnStrategy()

            elif column_config == "unique_email":
                return UniqueEmailUpdateColumnStrategy()

            elif column_config == "unique_login":
                return UniqueLoginUpdateColumnStrategy()

            else:
                # in autodetect, the column config string will be the fake_type
                return FakeUpdateColumnStrategy(self.fake_seeder, column_config)
        else:
            raise UnknownColumnStrategyError(column_config)

    def __parse_table(self, table_name, table_config):
        # string shorthand detection
        if isinstance(table_config, str):
            if table_config == "truncate":
                return TruncateTableStrategy()
            else:
                raise UnknownTableStrategyError(table_config)

        # dict autodetection
        elif isinstance(table_config, dict):
            if "columns" in table_config:
                column_strategies = {}
                for column_name, column_config in table_config["columns"].items():
                    column_strategies[column_name] = self.__parse_update_column(column_name, column_config)

                return UpdateColumnsTableStrategy(column_strategies)
            else:
                raise UnknownTableStrategyError(table_config)

        else:
            raise UnknownTableStrategyError(table_config)

    def parse_config(self, config):
        table_strategies = {}
        for table_name, table_config in config["tables"].items():
            table_strategies[table_name] = self.__parse_table(table_name, table_config)

        return DatabaseStrategy(table_strategies)
