from faker import Faker
from pynonymizer.log import get_logger
import inspect
from enum import Enum

logger = get_logger(__name__)


class FakeDataType(Enum):
    STRING = "STRING"
    DATE = "DATE"
    DATETIME = "DATETIME"
    INT = "INT"


_FAKE_DATA_TYPES = {
    "first_name":      FakeDataType.STRING,
    "last_name":       FakeDataType.STRING,
    "name":            FakeDataType.STRING,
    "user_name":       FakeDataType.STRING,
    "email":           FakeDataType.STRING,
    "company_email":   FakeDataType.STRING,
    "phone_number":    FakeDataType.STRING,
    "company":         FakeDataType.STRING,
    "bs":              FakeDataType.STRING,
    "catch_phrase":    FakeDataType.STRING,
    "job":             FakeDataType.STRING,
    "city":            FakeDataType.STRING,
    "street_address":  FakeDataType.STRING,
    "postcode":        FakeDataType.STRING,
    "uri":             FakeDataType.STRING,
    "ipv4_private":    FakeDataType.STRING,
    "ipv4_public":     FakeDataType.STRING,
    "file_name":       FakeDataType.STRING,
    "file_path":       FakeDataType.STRING,
    "paragraph":       FakeDataType.STRING,
    "prefix":          FakeDataType.STRING,
    "random_int":      FakeDataType.INT,
    "date_of_birth":   FakeDataType.DATE,
    "future_date":     FakeDataType.DATE,
    "past_date":       FakeDataType.DATE,
    "future_datetime": FakeDataType.DATETIME,
    "past_datetime":   FakeDataType.DATETIME,
    "date":            FakeDataType.DATE,
    "user_agent":      FakeDataType.STRING
}


class UnsupportedFakeTypeError():
    def __init__(self, fake_type, kwargs=None):
        kwargs = {} if kwargs is None else kwargs
        super().__init__(f"Unsupported Fake type: {fake_type}: {kwargs.keys()}")
        self.fake_type = fake_type
        self.kwargs = kwargs


class FakeColumnGenerator:
    def __init__(self, locale="en_GB"):
        self.__faker = Faker(locale)

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
        return _FAKE_DATA_TYPES[method_name]

    def get_value(self, method_name, additional_kwargs=None):
        additional_kwargs = {} if additional_kwargs is None else additional_kwargs

        if not self.supports(method_name, additional_kwargs):
            raise UnsupportedFakeTypeError(method_name, additional_kwargs)

        method = getattr(self.__faker, method_name)

        return method(**additional_kwargs)


