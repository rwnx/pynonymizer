from enum import Enum
from pynonymizer.fake import UnsupportedFakeTypeError
from abc import ABC, abstractmethod
import hashlib


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
class UpdateColumnStrategy(ABC):
    def __init__(self, column_name, where=None):
        self.column_name = column_name
        self.where_condition = where


class EmptyUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.EMPTY


class UniqueLoginUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_LOGIN


class UniqueEmailUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.UNIQUE_EMAIL


class LiteralUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.LITERAL

    def __init__(self, column_name, value, where=None):
        super().__init__(column_name, where)
        self.value = value


class FakeUpdateColumnStrategy(UpdateColumnStrategy):
    strategy_type = UpdateColumnStrategyTypes.FAKE_UPDATE

    def __init__(
        self,
        column_name,
        fake_column_generator,
        fake_type,
        where=None,
        fake_args=None,
        sql_type=None,
    ):
        fake_args = {} if fake_args is None else fake_args
        super().__init__(column_name, where)
        self.fake_type = fake_type
        self.fake_args = fake_args
        self.__fake_column_generator = fake_column_generator
        self.sql_type = sql_type

        if not fake_column_generator.supports(fake_type, fake_args):
            raise UnsupportedFakeTypeError(fake_type, fake_args)

    @property
    def qualifier(self):
        """
        Generate a deterministic qualifier for this fake update column strategy, so that it and it's args can be
        identified in cases like pre-generation of values
        e.g. file_path_depth_1
        :return:
        """
        sorted_args = "_".join(
            [
                f"{arg}_{value}"
                for arg, value in sorted(
                    self.fake_args.items(), key=lambda item: item[0]
                )
            ]
        )
        args_hash = hashlib.md5(bytes(sorted_args, "utf8")).hexdigest()

        # keep the whole thing below 64chars for maximum database compatibility
        return (self.fake_type + (("_" + args_hash) if sorted_args else ""))[:64]

    @property
    def value(self):
        """
        Generate a value from the faker data this column represents
        :return:
        """
        return self.__fake_column_generator.get_value(self.fake_type, self.fake_args)

    @property
    def data_type(self):
        """
        get this generator's data type
        e.g. FakeDataTypes.STRING
        :return:
        """
        return self.__fake_column_generator.get_data_type(self.fake_type)
