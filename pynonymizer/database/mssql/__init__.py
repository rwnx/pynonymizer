from pynonymizer.database.provider import DatabaseProvider


class MsSqlProvider(DatabaseProvider):
    def __init__(self, db_host, db_user, db_pass, db_name):
        pass

    def test_connection(self):
        pass

    def create_database(self):
        pass

    def drop_database(self):
        pass

    def anonymize_database(self, database_strategy):
        pass

    def restore_database(self, input_obj):
        pass

    def dump_database(self, output_obj):
        pass