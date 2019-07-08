from pynonymizer.strategy.table import TableStrategyTypes

class DatabaseStrategy:
    def __init__(self, table_strategies=None, scripts=None):

        self.__table_strategies = table_strategies or []
        self.__scripts = scripts or []

    @property
    def table_strategies(self):
        return self.__table_strategies

    @property
    def scripts(self):
        return self.__scripts

    @property
    def column_strategies(self):
        column_strategies = {}
        for table_strategy in self.__table_strategies:
            if table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
                column_strategies.update(table_strategy.column_strategies)

        return column_strategies

    def get_all_column_strategies(self):
        """LEGACY: move to property"""
        return self.column_strategies
