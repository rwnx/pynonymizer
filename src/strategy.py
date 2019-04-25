from enum import Enum
"""
A strategy is an container of instructions on how to anonymize a database.
            
        
"""

class UpdateColumnStrategyType(Enum):
    EMPTY = "empty"
    FAKE = "fake"
    FAKE_UNIQUE = "fake_unique"

class TableStrategyType(Enum):
    TRUNCATE = "truncate"
    UPDATE = "update"


class UnknownUpdateColumnFakeTypeError(Exception):
    def __init__(self, config):
        super().__init__("Unknown fake column type: {}".format(config))


class UpdateColumnStrategy:
    def __init__(self, name, fake_seeder, config):
        self.name = name
        if config in fake_seeder.supported_columns.keys():
            self.fake_type = config
        else:
            raise UnknownUpdateColumnFakeTypeError(config)

class TableStrategy:
    def __init__(self, name, fake_seeder, config):
        self.name = name
        self.columns = {}

        # auto-detect 'update' if given columns dict
        if isinstance(config, dict):
            if config["columns"]:
                self.type = "update"
                for column_name in config["columns"]:
                    self.columns[column_name] = UpdateColumnStrategy(column_name, fake_seeder, config["columns"][column_name])
            else:
                raise ValueError("Unable to autodetect or unknown table strategy")

        # auto-detect table wide strategies if passed string
        elif isinstance(config, str):
            if config == "truncate":
                self.type = "truncate"
            else:
                raise ValueError("Unknown table-wide strategy {}".format(config))

        else:
            raise ValueError("Could not parse table strategy. supported input types are str or dict")

    def get_required_fake_types(self):
        result_list = []
        if self.type == "update":
            for column in self.columns.values():
                result_list.append(column.fake_type)

        return result_list

    def get_column_strategies(self):
        return self.columns.values()


class DatabaseStrategy:
    def __init__(self, fake_seeder, config):
        self.tables = {}
        for table_name in config["tables"]:
            self.tables[table_name] = TableStrategy(table_name, fake_seeder, config["tables"][table_name])

    def get_required_fake_types(self):
        result_list = []
        for table in self.tables.values():
            result_list = result_list + table.get_required_fake_types()

        return result_list

    def get_table_strategies(self):
        return self.tables.values()
