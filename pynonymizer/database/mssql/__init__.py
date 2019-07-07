from pynonymizer.database.provider import DatabaseProvider
import pyodbc
from tqdm import tqdm
from pynonymizer.log import get_logger


class MsSqlProvider(DatabaseProvider):
    """
    A pyodbc-based MSSQL provider.
    """
    logger = get_logger(__name__)

    def __init__(self, db_host, db_user, db_pass, db_name):
        # MsSql only works with local db server because of backup file location requirements
        db_host = "(local)"
        super().__init__(db_host, db_user, db_pass, db_name)

    def __connection(self):
        return pyodbc.connect(f"DRIVER={{SQL Server}};SERVER={self.db_host};UID={self.db_user};PWD={self.db_pass}")

    def __db_connection(self):
        return pyodbc.connect(f"DRIVER={{SQL Server}};DATABASE={self.db_name};SERVER={self.db_host};UID={self.db_user};PWD={self.db_pass}")

    def __execute(self, *args, **kwargs):
        return self.__connection().execute(*args, **kwargs)

    def __db_execute(self, *args, **kwargs):
        return self.__db_connection().execute(*args, **kwargs)

    def test_connection(self):
        try:
            self.__execute("SELECT @@VERSION;").fetchall()
            return True
        except pyodbc.Error:
            return False

    def create_database(self):
        self.logger.debug("MSSQL: create_database ignored, database will be created when the database is restored")

    def drop_database(self):
        self.__execute("DROP DATABASE IF EXISTS [{self.db_name}];")

    def anonymize_database(self, database_strategy):
        pass

    def restore_database(self, input_path):
        # use RESTORE FILEGROUP to discover files and construct MOVE statements to tmpdir

        # restore, loop using nextset() - if using STATS = 1, should be 100 percentile results sets and 3 summary ones.
        pass

    def dump_database(self, output_path):
        self.__execute(f"BACKUP DATABASE [{self.db_name}] TO DISK {output_path};")

