from abc import ABC, abstractmethod

SEED_TABLE_NAME = "_pynonymizer_seed_fake_data"

class DatabaseProvider(ABC):
    @abstractmethod
    def __init__(self, db_host, db_user, db_pass, db_name, seed_rows=None):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name

        if seed_rows is None:
            seed_rows = 150

        self.seed_rows = int(seed_rows)

    @abstractmethod
    def test_connection(self):
        pass

    @abstractmethod
    def create_database(self):
        pass

    @abstractmethod
    def drop_database(self):
        pass

    @abstractmethod
    def anonymize_database(self, database_strategy):
        pass

    @abstractmethod
    def restore_database(self, input_obj):
        pass

    @abstractmethod
    def dump_database(self, output_obj):
        pass

def something(parser):
    ("--fake-locale", "-l")
    {
        "default":os.getenv("PYNONYMIZER_FAKE_LOCALE") or os.getenv("FAKE_LOCALE"),
        "help": "Locale setting to initialize fake data generation. Affects Names, addresses, formats, etc. [$PYNONYMIZER_FAKE_LOCALE]"
    }

class ProviderArg():
    def __init__(self, name, description):
