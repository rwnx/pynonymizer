from abc import ABC, abstractmethod

class DatabaseProvider(ABC):
    @abstractmethod
    def __init__(self, db_host, db_user, db_pass, db_name):
        pass

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
