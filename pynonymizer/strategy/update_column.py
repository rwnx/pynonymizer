from enum import Enum


class ColumnStrategyTypes(Enum):
    EMPTY = "EMPTY"
    UNIQUE_LOGIN = "UNIQUE_LOGIN"
    UNIQUE_EMAIL = "UNIQUE_EMAIL"
    FAKE_UPDATE = "FAKE_UPDATE"


# boilerplate abstract class for future use
class UpdateColumnStrategy:
    pass


class EmptyUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = ColumnStrategyTypes.EMPTY


class UniqueLoginUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = ColumnStrategyTypes.UNIQUE_LOGIN


class UniqueEmailUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = ColumnStrategyTypes.UNIQUE_EMAIL


class FakeUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = ColumnStrategyTypes.FAKE_UPDATE

    def __init__(self, fake_seeder, fake_type):
        self.fake_column = fake_seeder.get_fake_column(fake_type)
