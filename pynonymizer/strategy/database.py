from pynonymizer.strategy.table import UpdateColumnsTableStrategy
from pynonymizer.strategy.update_column import FakeUpdateColumnStrategy


class DatabaseStrategy:
    def __init__(self, table_strategies):
        self.table_strategies = table_strategies

    def get_update_column_fake_types(self):
        unique_fake_types = set()
        for table_name, table_strategy in self.table_strategies.items():
            if isinstance(table_strategy, UpdateColumnsTableStrategy):
                for column_name, column_strategy in table_strategy.column_strategies.items():
                    if isinstance(column_strategy, FakeUpdateColumnStrategy):
                        unique_fake_types.add(column_strategy.fake_type)

        return unique_fake_types

