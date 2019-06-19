from enum import Enum


class UpdateColumnStrategyTypes(Enum):
    EMPTY = "EMPTY"
    UNIQUE_LOGIN = "UNIQUE_LOGIN"
    UNIQUE_EMAIL = "UNIQUE_EMAIL"
    FAKE_UPDATE = "FAKE_UPDATE"

    @staticmethod
    def from_value(string):
        """
        a method to get an enum value from it's case-insensitive value.
        """
        try:
            return UpdateColumnStrategyTypes(string.upper())
        except ValueError:
            return None


# boilerplate abstract class for future use
class UpdateColumnStrategy:
    def __init__(self, where_condition=None):
        self.where_condition = where_condition


class EmptyUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.EMPTY


class UniqueLoginUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_LOGIN


class UniqueEmailUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_EMAIL


class FakeUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.FAKE_UPDATE

    def __init__(self, fake_seeder, fake_type, where_condition=None):
        super().__init__(where_condition)
        self.fake_type = fake_type
        self.fake_column = fake_seeder.get_fake_column(fake_type)
