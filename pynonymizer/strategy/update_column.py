from enum import Enum
from pynonymizer.fake import  UnsupportedFakeTypeError


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

    def __init__(self, fake_column_generator, fake_type, where=None, fake_args=None):
        fake_args = {} if fake_args is None else fake_args
        super().__init__(where)
        self.fake_type = fake_type
        self.fake_args = fake_args
        self.__fake_column_generator = fake_column_generator

        if not fake_column_generator.supports(fake_type, fake_args):
            raise UnsupportedFakeTypeError(fake_type, fake_args)

    def get_value(self):
        return self.__fake_column_generator.get_value(self.fake_type, self.fake_args)

    def get_data_type(self):
        return self.__fake_column_generator.get_data_type(self.fake_type)
