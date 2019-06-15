class DatabaseStrategy:
    def __init__(self, table_strategies=None, scripts=None):

        self.table_strategies = table_strategies or {}
        self.scripts = scripts or {}

    def get_fake_columns(self):
        unique_fake_types = set()
        for table_name, table_strategy in self.table_strategies.items():
            try:
                unique_fake_types = unique_fake_types.union( table_strategy.get_fake_columns() )
            except AttributeError as error:
                pass

        return unique_fake_types

