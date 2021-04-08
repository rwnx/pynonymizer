from abc import ABC, abstractmethod

SEED_TABLE_NAME = "_pynonymizer_seed_fake_data"

class DatabaseProvider(ABC):
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
