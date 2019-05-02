from enum import Enum


class ColumnStrategyTypes(Enum):
    EMPTY = "EMPTY"
    UNIQUE_LOGIN = "UNIQUE_LOGIN"
    UNIQUE_EMAIL = "UNIQUE_EMAIL"
    FAKE_UPDATE = "FAKE_UPDATE"


class UnsupportedFakeTypeError(Exception):
    def __init__(self, fake_type):
        super().__init__(f"Unsupported Fake type: {fake_type}")
        self.fake_type = fake_type


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
        if not fake_seeder.supports_fake_type(fake_type):
            raise UnsupportedFakeTypeError(fake_type)
        self.fake_column = fake_seeder.get_fake_column(fake_type)
