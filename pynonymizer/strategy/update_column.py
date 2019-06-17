from enum import Enum


class UpdateColumnStrategyTypes(Enum):
    EMPTY = "EMPTY"
    UNIQUE_LOGIN = "UNIQUE_LOGIN"
    UNIQUE_EMAIL = "UNIQUE_EMAIL"
    FAKE_UPDATE = "FAKE_UPDATE"


# boilerplate abstract class for future use
class UpdateColumnStrategy:
    pass


class EmptyUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.EMPTY


class UniqueLoginUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_LOGIN


class UniqueEmailUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_EMAIL


class FakeUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.FAKE_UPDATE

    def __init__(self, fake_seeder, fake_type):
        self.fake_column = fake_seeder.get_fake_column(fake_type)
