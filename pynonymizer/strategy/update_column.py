from enum import Enum


class UpdateColumnStrategyTypes(Enum):
    EMPTY = "EMPTY"
    UNIQUE_LOGIN = "UNIQUE_LOGIN"
    UNIQUE_EMAIL = "UNIQUE_EMAIL"
    FAKE_UPDATE = "FAKE_UPDATE"
    LITERAL = "LITERAL"

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
    def __init__(self, where=None):
        self.where_condition = where


class EmptyUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.EMPTY


class UniqueLoginUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_LOGIN


class UniqueEmailUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_EMAIL


class LiteralUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.LITERAL

    def __init__(self, value, where=None):
        super().__init__(where)
        self.value = value


class FakeUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.FAKE_UPDATE

    def __init__(self, fake_seeder, fake_type, where=None):
        super().__init__(where)
        self.fake_type = fake_type
        self.fake_column = fake_seeder.get_fake_column(fake_type)
