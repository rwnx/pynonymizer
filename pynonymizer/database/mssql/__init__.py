from pynonymizer.database.provider import DatabaseProvider
import pyodbc
import math
from tqdm import tqdm
import os
from pathlib import Path
from pynonymizer.log import get_logger


class MsSqlProvider(DatabaseProvider):
    """
    A pyodbc-based MSSQL provider.
    """
    logger = get_logger(__name__)
    __STATS = 5

    def __init__(self, db_host, db_user, db_pass, db_name, seed_rows=None):
        if db_host is not None:
            raise ValueError("MsSqlProvider does not support remove servers due to backup file location requirements. "
                             "You must omit db_host from your configuration and run pynonymizer on the same "
                             "server as the database.")

        db_host = "(local)"
        super().__init__(db_host, db_user, db_pass, db_name, seed_rows)
        self.__conn = None
        self.__db_conn = None

    def __connection(self):
        """a lazy-evaluated connection"""
        if self.__conn is None:
            self.__conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={self.db_host};UID={self.db_user};PWD={self.db_pass}", autocommit=True
            )

        return self.__conn

    def __db_connection(self):
        """a lazy-evaluated db-specific connection"""
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
        It's possible that the model database is not the currently set default, i.e if it's been changed after install
        The solution to this would be to make a new database and then perform the below check on that instead.
        See https://blogs.technet.microsoft.com/sqlman/2009/07/19/tsql-script-determining-default-database-file-log-path/

        However, this seems like a heavyweight solution for what is essentially a tsql-writeable tempfolder, so
        checking the model db seems like a good 'boring' solution
        :return: Default data directory e.g. "C:\\DATA"
        """
        datafile = self.__execute("""
        SELECT physical_name   
        FROM sys.master_files mf   
        INNER JOIN sys.[databases] d   
        ON mf.[database_id] = d.[database_id]   
        WHERE d.[name] = 'model' AND type = 0
        """).fetchone()[0]

        return Path(datafile).parent

    def __get_default_logfolder(self):
        """
        Locate the default log folder using the `model` database location
        __get_default_datafolder: see for more info
        :return:
        """
        logfile = self.__execute("""
        SELECT physical_name   
        FROM sys.master_files mf   
        INNER JOIN sys.[databases] d   
        ON mf.[database_id] = d.[database_id]   
        WHERE d.[name] = 'model' AND type = 1
        """).fetchone()[0]

        return Path(logfile).parent

    def __get_file_moves(self, input_path):
        """
        Using RESTORE FILELISTONLY, get all the files in the backup that need to be moved to the local system for restore
        :return: a dict of file name: new destination
        """
        datadir = self.__get_default_datafolder()
        logdir = self.__get_default_logfolder()

        filelist = self.__execute(f"RESTORE FILELISTONLY FROM DISK = ?;", input_path).fetchall()

        move_file_map = {}
        for file in filelist:
            name = file[0]
            type = file[2].upper()
            filepath = Path(file[1])

            # log files can go into the default log directory, everything else can go into the data directory
            if type == "L":
                target_path = str(logdir.joinpath(f"{self.db_name}_{filepath.name}"))
            else:
                target_path = str(datadir.joinpath(f"{self.db_name}_{filepath.name}"))

            move_file_map[name] = target_path

        return move_file_map

    def __async_operation_progress(self, desc, cursor):
        # With STATS=x, we should recieve 100/x resultsets, provided the backup is slow enough.
        # With some databases, it will jump from y% to 100, so we'll only get <x nextset calls.
        # Even SSMS doesn't get informed - this is the best we can do at the moment
        with tqdm(desc=desc, total=math.floor(100 / self.__STATS)) as progressbar:
            while cursor.nextset():
                progressbar.update()

            # finish the progress - less confusing than a dangling 40% progressbar
            progressbar.update(progressbar.total - progressbar.n)

    def test_connection(self):
        try:
            self.__execute("SELECT @@VERSION;").fetchall()
            return True
        except pyodbc.Error:
            return False

    def create_database(self):
        self.logger.warning("MSSQL: create_database ignored, database will be created when the database is restored")

    def drop_database(self):
        self.__execute(f"DROP DATABASE IF EXISTS [{self.db_name}];")

    def anonymize_database(self, database_strategy):
        self.logger.warning("MSSQL: anonymize_database not yet implemented")

    def restore_database(self, input_path):
        move_files = self.__get_file_moves(input_path)

        self.logger.info("Found %d files", len(move_files) )

        # get move statements and flatten pairs out so we can do the 2-param substitution
        move_clauses = ", ".join( ["MOVE ? TO ?"] * len(move_files) )
        move_clause_params = [item for pair in move_files.items() for item in pair]

        restore_cursor = self.__execute(f"RESTORE DATABASE ? FROM DISK = ? WITH {move_clauses}, STATS = ?;",
                                        [self.db_name, input_path, *move_clause_params, self.__STATS])

        self.__async_operation_progress("Restoring Database", restore_cursor)

    def dump_database(self, output_path):
        dump_cursor = self.__execute(f"BACKUP DATABASE ? TO DISK = ? WITH STATS = ?;", [self.db_name, output_path, self.__STATS])
        self.__async_operation_progress("Dumping Database", dump_cursor)

