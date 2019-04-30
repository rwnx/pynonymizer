from faker import Faker
from functools import reduce
from tqdm import tqdm
from pynonymizer.log import get_logger
logger = get_logger(__name__)


def _map_fake_columns(fake_columns):
    """
    map a list of FakeColumn instances to a map of name: FakeColumn
     {
      "first_name": FakeColumn("first_name[...]
    :param fake_columns: A list of FakeColumn instances
    :return:
    """
    return reduce(lambda result, col: (result.update({col.name: col}) or result), fake_columns, {})


class FakeColumn:
    def __init__(self, faker_instance, name, sql_type, generator=None):
        self.name = name
        self.sql_type = sql_type
        if generator is None:
            fake_attr = getattr(faker_instance, name)
            self.generator = lambda: fake_attr()
        else:
            self.generator = generator

    def get_value(self):
        return self.generator()


class FakeSeeder:
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

    # TODO: this is a DB concern, really. faker/fakedata shouldn't be indicating the process of building the seed table
    # move to database providers
    def seed(self, database, database_strategy, seed_rows=150):
        """
        'Seed' the database with a bunch of pre-generated random records so updates can be performed in batch updates
        """
        # Filter supported columns so we're not seeding ALL types by default
        required_columns = database_strategy.get_update_column_fake_types()
        filtered_columns = set([value for value in self.supported_columns.values() if value.name in required_columns])

        if len(filtered_columns) < 1:
            raise ValueError("Resulting seed columns is empty. All of the columns specified were unsupported ")

        logger.info("creating seed table...")
        logger.debug(f"seed table columns: {filtered_columns}")

        database.create_seed_table(filtered_columns)

        for i in tqdm(range(0, seed_rows), desc="Inserting seed data", unit="rows"):
            logger.debug(f"inserting seed row {i}")
            database.insert_seed_row(filtered_columns)


