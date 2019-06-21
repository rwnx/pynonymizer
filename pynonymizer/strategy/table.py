from enum import Enum


class TableStrategyTypes(Enum):
    TRUNCATE = "TRUNCATE"
    UPDATE_COLUMNS = "UPDATE_COLUMNS"

    @staticmethod
    def from_value(string):
        try:
            return TableStrategyTypes(string.upper())
        except ValueError:
            return None


# boilerplate abstract class for future use
class TableStrategy():
    pass


class TruncateTableStrategy(TableStrategy):
    strategy_type = TableStrategyTypes.TRUNCATE
    pass


class UpdateColumnsTableStrategy(TableStrategy):
    strategy_type = TableStrategyTypes.UPDATE_COLUMNS

    def __init__(self, column_strategies):
        self.column_strategies = column_strategies

    def get_column_strategies(self):
        column_strategies = {}
        for column_name, column_strategy in self.column_strategies.items():
            column_strategies[column_name] = column_strategy

        return column_strategies
