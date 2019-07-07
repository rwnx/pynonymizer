from pynonymizer.database.provider import DatabaseProvider
import pyodbc
import math
from tqdm import tqdm
import os
from pynonymizer.log import get_logger


class MsSqlProvider(DatabaseProvider):
    """
    A pyodbc-based MSSQL provider.
    """
    logger = get_logger(__name__)
    __STATS = 5

    def __init__(self, db_host, db_user, db_pass, db_name, seed_rows=None):
        # MsSql only works with local db server because of backup file location requirements
        db_host = "(local)"
        super().__init__(db_host, db_user, db_pass, db_name, seed_rows)
        self.__conn = None
        self.__db_conn = None

    def __connection(self):
        """
        a lazy-evaluated connection
        :return:
        """
        if self.__conn is None:
            self.__conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={self.db_host};UID={self.db_user};PWD={self.db_pass}", autocommit=True
            )

        return self.__conn

    def __db_connection(self):
        """
        a lazy-evaluated db-specific connection
        :return:
        """
        if self.__db_conn is None:
            self.__db_conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};DATABASE={self.db_name};SERVER={self.db_host};UID={self.db_user};PWD={self.db_pass}",
                autocommit=True
            )

        return self.__db_conn

    def __execute(self, *args, **kwargs):
        return self.__connection().execute(*args, **kwargs)

    def __db_execute(self, *args, **kwargs):
        return self.__db_connection().execute(*args, **kwargs)

    def __get_default_datafolder(self):
        """
        Locate the default data folder using the `model` database location
        :return:
        """
        datafile = self.__execute("""
        SELECT physical_name   
        FROM sys.master_files mf   
        INNER JOIN sys.[databases] d   
        ON mf.[database_id] = d.[database_id]   
        WHERE d.[name] = 'model' AND type = 0
        """).fetchone()[0]

        return os.path.dirname(datafile)

    def __get_default_logfolder(self):
        """
        Locate the default log folder using the `model` database location
        :return:
        """
        logfile = self.__execute("""
        SELECT physical_name   
        FROM sys.master_files mf   
        INNER JOIN sys.[databases] d   
        ON mf.[database_id] = d.[database_id]   
        WHERE d.[name] = 'model' AND type = 1
        """).fetchone()[0]

        return os.path.dirname(logfile)

    def __get_file_moves(self, input_path):
        """
        Using RESTORE FILELISTONLY, get a list of all the files in the backup that need to be moved to the local system
        """
        datadir = self.__get_default_datafolder()
        logdir = self.__get_default_logfolder()

        filelist = self.__execute(f"RESTORE FILELISTONLY FROM DISK = ?;", input_path).fetchall()

        move_clauses = []
        move_clause_params = []
        for file in filelist:
            name = file[0]
            full_path = file[1]
            basename = os.path.basename(full_path)
            _, ext = os.path.splitext(basename)

            if ext.lower() == "ldf":
                target_path = os.path.join(logdir, f"{self.db_name}_{basename}")
            else:
                target_path = os.path.join(datadir, f"{self.db_name}_{basename}")

            move_clauses.append(f"MOVE ? TO ?")
            move_clause_params.append(name)
            move_clause_params.append(target_path)

        return move_clauses, move_clause_params

    def __backup_restore_progress(self, cursor):
        # With STATS=5, we should recieve 20 resultsets, provided the backup is slow enough.
        # With some databases, it will jump from xx% to 100, so we'll only get 40x nextset calls.
        # Even SSMS doesn't get informed - this is the best we can do at the moment
        with tqdm(desc="Restoring database", total=math.floor(100 / self.__STATS)) as progressbar:
            while cursor.nextset():
                progressbar.update()

            # finish the progress - less confusing than a dangling 40% progressbar
            progressbar.update(tqdm.total - tqdm.n)

    def test_connection(self):
        try:
            self.__execute("SELECT @@VERSION;").fetchall()
            return True
        except pyodbc.Error:
            return False

    def create_database(self):
        self.logger.debug("MSSQL: create_database ignored, database will be created when the database is restored")

    def drop_database(self):
        self.__execute(f"DROP DATABASE IF EXISTS ?;", [self.db_name])

    def anonymize_database(self, database_strategy):
        pass

    def restore_database(self, input_path):
        move_clauses, move_clause_params = self.__get_file_moves(input_path)

        move_statement_combined = ", ".join(move_clauses)

        restore_cursor = self.__execute(f"RESTORE DATABASE ? FROM DISK = ? WITH {move_statement_combined}, STATS = ?;",
                                        [self.db_name, input_path, *move_clause_params, self.__STATS])

        self.__backup_restore_progress(restore_cursor)

    def dump_database(self, output_path):
        dump_cursor = self.__execute(f"BACKUP DATABASE ? TO DISK = ? WITH STATS = 5;", [self.db_name, output_path])
        self.__backup_restore_progress(dump_cursor)

