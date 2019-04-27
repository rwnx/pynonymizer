class TableStrategy():
    pass


class TruncateTableStrategy(TableStrategy):
    pass


class UpdateColumnsTableStrategy(TableStrategy):
    def __init__(self, column_strategies):
        self.column_strategies = column_strategies
