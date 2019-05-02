from enum import Enum


class TableStrategyTypes(Enum):
    TRUNCATE = "TRUNCATE"
    UPDATE_COLUMNS = "UPDATE_COLUMNS"


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

    def get_fake_columns(self):
        unique_fake_types = set()
        for column_name, column_strategy in self.column_strategies.items():
            try:
                unique_fake_types.add(column_strategy.fake_column)
            except AttributeError as error:
                pass

        return unique_fake_types
