from pynonymizer.strategy.table import TableStrategyTypes
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes


class DatabaseStrategy:
    def __init__(self, table_strategies=None, before_scripts=None, after_scripts=None):
        self.table_strategies = []
        self.before_scripts = []
        self.after_scripts = []

        for table_strat in table_strategies:
            self.table_strategies.append(table_strat)

        if before_scripts:
            for script in before_scripts:
                self.before_scripts.append(script)

        if after_scripts:
            for script in after_scripts:
                self.after_scripts.append(script)

    @property
    def scripts(self):
        """
        Deprecated - use before/after vars
        :return:
        """
        return {"before": self.before_scripts, "after": self.after_scripts}

    @property
    def fake_update_qualifier_map(self):
        column_strategies = {}
        for table_strategy in self.table_strategies:
            if table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
                for column_strategy in table_strategy.column_strategies:
                    if (
                        column_strategy.strategy_type
                        == UpdateColumnStrategyTypes.FAKE_UPDATE
                    ):
                        column_strategies[column_strategy.qualifier] = column_strategy

        return column_strategies

    @property
    def all_column_strategies(self):
        column_strategies = {}
        for table_strategy in self.table_strategies:
            if table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
                column_strategies += table_strategy.column_strategies

        return column_strategies

    def get_all_column_strategies(self):
        """LEGACY: move to property"""
        return self.all_column_strategies
