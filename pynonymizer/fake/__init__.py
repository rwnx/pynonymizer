from faker import Faker
import logging
import inspect
from enum import Enum
import importlib

logger = logging.getLogger(__name__)


class FakeDataType(Enum):
    STRING = "STRING"
    DATE = "DATE"
    DATETIME = "DATETIME"
    INT = "INT"


"""
We have to create a mapping here between faker types and rough return values, because providers need to know how to
Store the generated values in the 'seed' table.

FakeColumnGenerator will assume STRING unless the below mapping overrides it.
"""
_FAKE_DATA_TYPES = {
    # date_time
    "random_int": FakeDataType.INT,
    "date_between": FakeDataType.DATE,
    "date_between_dates": FakeDataType.DATE,
    "date_object": FakeDataType.DATE,
    "date_of_birth": FakeDataType.DATE,
    "date_this_century": FakeDataType.DATE,
    "date_this_decade": FakeDataType.DATE,
    "date_this_month": FakeDataType.DATE,
    "date_this_year": FakeDataType.DATE,
    "date_time": FakeDataType.DATETIME,
    "date_time_ad": FakeDataType.DATETIME,
    "date_time_between": FakeDataType.DATETIME,
    "date_time_between_dates": FakeDataType.DATETIME,
    "date_time_this_century": FakeDataType.DATETIME,
    "date_time_this_decade": FakeDataType.DATETIME,
    "date_time_this_month": FakeDataType.DATETIME,
    "date_time_this_year": FakeDataType.DATETIME,
    "future_date": FakeDataType.DATE,
    "future_datetime": FakeDataType.DATETIME,
    "past_date": FakeDataType.DATE,
    "past_datetime": FakeDataType.DATETIME,
    "date": FakeDataType.DATE,
}


class UnsupportedFakeTypeError(Exception):
    def __init__(self, fake_type, kwargs=None):
        kwargs = {} if kwargs is None else kwargs
        super().__init__(f"Unsupported Fake type: {fake_type}")
        self.fake_type = fake_type
        self.kwargs = kwargs


class UnsupportedFakeArgumentsError(UnsupportedFakeTypeError):
    def __init__(self, fake_type, kwargs=None):
        kwargs = {} if kwargs is None else kwargs
        super().__init__(f'Unsupported Fake Arguments for "{fake_type}": {kwargs}')
        self.fake_type = fake_type
        self.kwargs = kwargs


class FakeColumnGenerator:
    def __init__(self, locale=None, providers=[]):
        self.__faker = Faker(locale)

        for provider_path in providers:
            module_path, cls_name = provider_path.rsplit(".", 1)
            imported = importlib.import_module(module_path)
            imported_cls = getattr(imported, cls_name)
            self.__faker.add_provider(imported_cls)

    def supports(self, method_name, additional_kwargs=None):
        additional_kwargs = {} if additional_kwargs is None else additional_kwargs
        try:
            method = getattr(self.__faker, method_name)
        except AttributeError:
            return False

        argspec = inspect.getfullargspec(method)
        if all(kwarg in argspec.args for kwarg in additional_kwargs):
            return True
        else:
            return False

    def get_data_type(self, method_name):
        """Get the datatype for a column's method_name"""
        try:
            return _FAKE_DATA_TYPES[method_name]
        except KeyError:
            return FakeDataType.STRING

    def get_value(self, method_name, additional_kwargs=None):
        """
        Get a value from a fake column using the appropriate faker method and it's kwargs
        """
        additional_kwargs = {} if additional_kwargs is None else additional_kwargs

        try:
            method = getattr(self.__faker, method_name)
        except AttributeError:
            raise UnsupportedFakeTypeError(method_name, additional_kwargs)

        argspec = inspect.getfullargspec(method)
        if not all(kwarg in argspec.args for kwarg in additional_kwargs):
            raise UnsupportedFakeArgumentsError(method_name, additional_kwargs)

        return method(**additional_kwargs)
