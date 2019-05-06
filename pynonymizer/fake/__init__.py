from faker import Faker
from functools import reduce
from pynonymizer.log import get_logger
logger = get_logger(__name__)


class UnsupportedFakeTypeError(KeyError):
    def __init__(self, fake_type):
        super().__init__(f"Unsupported Fake type: {fake_type}")
        self.fake_type = fake_type


def _map_fake_columns(fake_columns):
    """
    map a list of FakeColumn instances to a map of name: FakeColumn
     {
      "first_name": FakeColumn("first_name[...]
    :param fake_columns: A list of FakeColumn instances
    :return:
    """
    return reduce(lambda result, col: (result.update({col.column_name: col}) or result), fake_columns, {})


class FakeColumn:
    def __init__(self, faker_instance, column_name, sql_type, generator=None):
        self.column_name = column_name
        self.sql_type = sql_type
        if generator is None:
            fake_attr = getattr(faker_instance, column_name)
            self.generator = lambda: fake_attr()
        else:
            self.generator = generator

    def get_value(self):
        return self.generator()


class FakeColumnSet:
    def __init__(self, locale="en_GB"):
        self.faker = Faker(locale)
        self.supported_columns = _map_fake_columns([
            FakeColumn(self.faker, "first_name", "VARCHAR(50)"),
            FakeColumn(self.faker, "last_name", "VARCHAR(50)"),
            FakeColumn(self.faker, "name", "VARCHAR(50)"),
            FakeColumn(self.faker, "user_name", "VARCHAR(50)"),
            FakeColumn(self.faker, "email", "VARCHAR(50)"),
            FakeColumn(self.faker, "company_email", "VARCHAR(50)"),
            FakeColumn(self.faker, "phone_number", "VARCHAR(50)"),
            FakeColumn(self.faker, "company", "VARCHAR(50)"),
            FakeColumn(self.faker, "bs", "VARCHAR(150)"),
            FakeColumn(self.faker, "catch_phrase", "VARCHAR(150)"),
            FakeColumn(self.faker, "job", "VARCHAR(50)"),
            FakeColumn(self.faker, "city", "VARCHAR(50)"),
            FakeColumn(self.faker, "street_address", "VARCHAR(50)"),
            FakeColumn(self.faker, "postcode", "VARCHAR(50)"),
            FakeColumn(self.faker, "uri", "VARCHAR(150)"),
            FakeColumn(self.faker, "ipv4_private", "VARCHAR(50)"),
            FakeColumn(self.faker, "ipv4_public", "VARCHAR(50)"),
            FakeColumn(self.faker, "file_name", "VARCHAR(150)"),
            FakeColumn(self.faker, "file_path", "VARCHAR(150)"),
            FakeColumn(self.faker, "paragraph", "VARCHAR(255)"),
            FakeColumn(self.faker, "prefix", "VARCHAR(10)"),
            FakeColumn(self.faker, "random_int", "INT"),
            FakeColumn(self.faker, "date_of_birth", "DATE"),
            FakeColumn(self.faker, "future_date", "DATE"),
            FakeColumn(self.faker, "past_date", "DATE"),
            FakeColumn(self.faker, "future_datetime", "DATETIME"),
            FakeColumn(self.faker, "past_datetime", "DATETIME"),
            FakeColumn(self.faker, "date", "DATE")
        ])

    def get_fake_column(self, fake_type):
        try:
            return self.supported_columns[fake_type]
        except KeyError as error:
            raise UnsupportedFakeTypeError(fake_type) from None



