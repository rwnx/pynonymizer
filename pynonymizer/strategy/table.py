from enum import Enum
from abc import ABC, abstractmethod


class TableStrategyTypes(Enum):
    TRUNCATE = "TRUNCATE"
    UPDATE_COLUMNS = "UPDATE_COLUMNS"
    DELETE = "DELETE"

    @staticmethod
    def from_value(string):
        try:
            return TableStrategyTypes(string.upper())
        except ValueError:
            return None


class TableStrategy(ABC):
    def __init__(self, table_name, schema=None):
        self.table_name = table_name
        self.schema = schema

    @property
    def qualified_name(self):
        return f"{self.schema}.{self.table_name}" if self.schema else self.table_name


class DeleteTableStrategy(TableStrategy):
    strategy_type = TableStrategyTypes.DELETE


class TruncateTableStrategy(TableStrategy):
    strategy_type = TableStrategyTypes.TRUNCATE


class UpdateColumnsTableStrategy(TableStrategy):
    strategy_type = TableStrategyTypes.UPDATE_COLUMNS

    def __init__(self, table_name, column_strategies, schema=None):
        super().__init__(table_name=table_name, schema=schema)
        self.__column_strategies = []
        for column_strategy in column_strategies:
            self.__column_strategies.append(column_strategy)

    def group_by_where(self):
        """
        returns a map of columns, grouped in a map of where conditions
        :return:
        """
        grouped_columns = {}

        for column_strategy in self.__column_strategies:
            where_condition = column_strategy.where_condition
            if where_condition not in grouped_columns:
                grouped_columns[where_condition] = {}

            grouped_columns[where_condition][
                column_strategy.column_name
            ] = column_strategy

        return grouped_columns

    @property
    def column_strategies(self):
        return self.__column_strategies

    def get_column_strategies(self):
        """Legacy, replace with property"""
        return self.column_strategies
