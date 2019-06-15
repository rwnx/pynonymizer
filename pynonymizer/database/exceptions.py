from pynonymizer.exceptions import PynonymizerError


class DatabaseProviderError(PynonymizerError):
    pass


class MissingPrerequisiteError(DatabaseProviderError):
    pass


class UnsupportedTableStrategyError(DatabaseProviderError):
    def __init__(self, table_strategy):
        super().__init__("Unsupported Table Strategy: {}".format(table_strategy))


class UnknownDatabaseTypeError(DatabaseProviderError):
    def __init__(self, database_type):
        self.database_type = database_type
        super().__init__("Unknown Database Type: {}".format(database_type))


class UnsupportedColumnStrategyError(DatabaseProviderError):
    def __init__(self, column_strategy):
        self.column_strategy = column_strategy
        super().__init__("Unsupported Column Strategy Type: {}".format(column_strategy))