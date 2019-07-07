class DatabaseStrategy:
    def __init__(self, table_strategies=None, scripts=None):

        self.__table_strategies = table_strategies or {}
        self.__scripts = scripts or {}

    @property
    def table_strategies(self):
        return self.__table_strategies

    @property
    def scripts(self):
        return self.__scripts

    def get_all_column_strategies(self):
        column_strategies = {}
        for table_name, table_strategy in self.table_strategies.items():
            try:
                table_columns = table_strategy.get_column_strategies()
                column_strategies.update( table_columns )
            except AttributeError as error:
                pass

        return column_strategies

