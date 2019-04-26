from enum import Enum
from pynonymizer.logging import get_logger
logger = get_logger(__name__)


"""
A strategy is an container of instructions on how to anonymize a database. 
"""


class UpdateColumnStrategyTypes(Enum):
    EMPTY = "empty"
    NULL = "null"
    FAKE = "fake"
    UNIQUE_EMAIL = "unique_email"
    UNIQUE_LOGIN = "unique_login"


class TableStrategyTypes(Enum):
    TRUNCATE = "truncate"
    UPDATE = "update"


class UnknownUpdateColumnFakeTypeError(Exception):
    def __init__(self, config):
        self.config = config
        super().__init__("Unknown fake column type: {}".format(config))


class UnknownTableStrategyError:
    def __init__(self, config):
        self.config = config
        super().__init__("Unable to determine table strategy from value: {}".format(config))


class UpdateColumnStrategy:
    def __init__(self, name, fake_seeder, config):
        self.name = name
        if config == "empty":
            self.type = UpdateColumnStrategyTypes.EMPTY

        elif config == "null":
            self.type = UpdateColumnStrategyTypes.NULL

        elif config == "unique_email":
            self.type = UpdateColumnStrategyTypes.UNIQUE_EMAIL

        elif config == "unique_login":
            self.type = UpdateColumnStrategyTypes.UNIQUE_LOGIN

        elif config in fake_seeder.supported_columns.keys():
            self.type = UpdateColumnStrategyTypes.FAKE
            self.fake_type = config

        else:
            raise UnknownUpdateColumnFakeTypeError(config)


class TableStrategy:
    def __init__(self, name, fake_seeder, config):
        self.name = name

        # auto-detect 'update' if given columns dict
        if isinstance(config, dict):
            if config["columns"]:
                self.type = TableStrategyTypes.UPDATE
                self.column_strategies = {}
                for column_name in config["columns"]:
                    self.column_strategies[column_name] = UpdateColumnStrategy(column_name, fake_seeder, config["columns"][column_name])
            else:
                raise UnknownTableStrategyError(config)

        # auto-detect table wide strategies if passed string
        elif isinstance(config, str):
            if config == "truncate":
                self.type = TableStrategyTypes.TRUNCATE
            else:
                raise UnknownTableStrategyError(config)

        else:
            raise UnknownTableStrategyError(config)

    def get_column_strategies(self):
        return self.column_strategies.values()


class DatabaseStrategy:
    def __init__(self, fake_seeder, config):
        self.table_strategies = {}
        for table_name in config["tables"]:
            self.table_strategies[table_name] = TableStrategy(table_name, fake_seeder, config["tables"][table_name])

    def get_update_column_fake_types(self):
        result_list = []
        for table_strategy in self.table_strategies.values():
            if table_strategy.type == TableStrategyTypes.UPDATE:
                for column_strategy in table_strategy.get_column_strategies():
                    if column_strategy.type == UpdateColumnStrategyTypes.FAKE:
                        result_list.append(column_strategy.fake_type)

        return result_list

    def get_table_strategies(self):
        return self.table_strategies.values()
