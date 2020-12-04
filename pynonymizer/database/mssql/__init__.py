from pynonymizer.database.provider import DatabaseProvider
from pynonymizer.database.provider import SEED_TABLE_NAME
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes
from pynonymizer.strategy.table import TableStrategyTypes
from pynonymizer.database.exceptions import UnsupportedColumnStrategyError, UnsupportedTableStrategyError, DependencyError
from pynonymizer.fake import FakeDataType

import math
from tqdm import tqdm
from pathlib import PureWindowsPath, PurePosixPath
from pynonymizer.log import get_logger

_FAKE_COLUMN_TYPES = {
    FakeDataType.STRING: "VARCHAR(MAX)",
    FakeDataType.DATE: "DATE",
    FakeDataType.DATETIME: "DATETIME",
    FakeDataType.INT: "INT"
}


class MsSqlProvider(DatabaseProvider):
    """
    A pyodbc-based MSSQL provider.
    """

    logger = get_logger(__name__)

    # stats value for restore/backup command: Report progress every X percent
    # A lower value means MORE resultssets / more frequent updates from the backup command.
    # Values lower than 5 often yield unreliable results on smaller backups
    __STATS = 5

    def __init__(self, db_host, db_user, db_pass, db_name, db_port=None, seed_rows=None, backup_compression=False):
        # import here for fast-failiness
        import pyodbc

        if db_host is not None:
            raise DependencyError("db_host", "MsSqlProvider does not support remote servers due to backup file "
                                             "location requirements. You must omit db_host from your configuration "
                                             "and run pynonymizer on the same server as the database.")

        # TODO: The odbc port syntax doesn't seem to work with (local),1433 or port=1433
        # TODO: This needs attention, but as it's backwards compatible, we're going to disallow it here.
        if db_port is not None:
            raise DependencyError("db_port", "MsSqlProvider does not support custom ports. You must omit db_port "
                                             "from your configuration to continue.")

        db_host = "(local)"

        super().__init__(db_host=db_host, db_user=db_user, db_pass=db_pass, db_name=db_name, db_port=db_port, seed_rows=seed_rows)
        self.__conn = None
        self.__db_conn = None
        self.__backup_compression = backup_compression

    def __connection(self):
        import pyodbc
        """a lazy-evaluated connection"""
        if self.__conn is None:
            self.__conn = pyodbc.connect(
                driver="{SQL Server Native Client 11.0}",
                server=self.db_host,
                uid=self.db_user,
                pwd=self.db_pass,
                autocommit=True
            )

        return self.__conn

    def __db_connection(self):
        import pyodbc
        """a lazy-evaluated db-specific connection"""
        if self.__db_conn is None:
            self.__db_conn = pyodbc.connect(
                driver="{SQL Server Native Client 11.0}",
                database=self.db_name,
                server=self.db_host,
                uid=self.db_user,
                pwd=self.db_pass,
                autocommit=True
            )

        return self.__db_conn

    def __execute(self, *args, **kwargs):
        return self.__connection().execute(*args, **kwargs)

    def __db_execute(self, *args, **kwargs):
        return self.__db_connection().execute(*args, **kwargs)

    def __get_path(self, filepath):
        if "\\" in filepath:
            return PureWindowsPath(filepath)
        else:
            return PurePosixPath(filepath)

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

        return self.__get_path(datafile).parent

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

        return self.__get_path(logfile).parent

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
            filepath = self.__get_path(file[1])

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
        # Even SSMS doesn't get informed (read: it's not my fault, blame microsoft)
        with tqdm(desc=desc, total=math.floor(100 / self.__STATS)) as progressbar:
            while cursor.nextset():
                progressbar.update()

            # finish the progress - less confusing than a dangling 40% progressbar
            progressbar.update(progressbar.total - progressbar.n)

    def __run_scripts(self, script_list, title=""):
        import pyodbc
        for i, script in enumerate(script_list):
            self.logger.info(f"Running f{title} script #{i} \"{script[:50]}\"")
            cursor = self.__db_execute(script)
            results = None
            try:
                results = cursor.fetchall()
            except pyodbc.Error:
                pass
            self.logger.info(results)

    def __create_seed_table(self, qualifier_map):
        seed_column_lines = ["[{}] {}".format(name, _FAKE_COLUMN_TYPES[col.data_type]) for name, col in qualifier_map.items()]
        create_statement = "CREATE TABLE [{}]({});".format(SEED_TABLE_NAME, ",".join(seed_column_lines))

        self.__db_execute(create_statement)

    def __drop_seed_table(self):
        self.__db_execute("DROP TABLE IF EXISTS [{}];".format(SEED_TABLE_NAME))

    def __insert_seed_row(self, qualifier_map):
        column_list = ",".join(["[{}]".format(qualifier) for qualifier in qualifier_map])
        substitution_list = ",".join([" ?".format(qualifier) for qualifier in qualifier_map])
        value_list = [column.value for qualifier, column in qualifier_map.items()]

        statement = "INSERT INTO [{}]({}) VALUES ({});".format(SEED_TABLE_NAME, column_list, substitution_list)
        self.__db_execute(statement, value_list)

    def __seed(self, qualifier_map):
        for i in tqdm(range(0, self.seed_rows), desc="Inserting seed data", unit="rows"):
            self.__insert_seed_row(qualifier_map)

    def __get_column_subquery(self, column_strategy):
        if column_strategy.strategy_type == UpdateColumnStrategyTypes.EMPTY:
            return "('')"
        elif column_strategy.strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL:
            return f"( SELECT CONCAT(NEWID(), '@', NEWID(), '.com') )"
        elif column_strategy.strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN:
            return f"( SELECT NEWID() )"
        elif column_strategy.strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE:
            column = f"[{column_strategy.qualifier}]"
            if column_strategy.sql_type:
                column = f"CAST({column} AS {column_strategy.sql_type})"
            return f"( SELECT TOP 1 {column} FROM [{SEED_TABLE_NAME}] ORDER BY NEWID())"
        elif column_strategy.strategy_type == UpdateColumnStrategyTypes.LITERAL:
            return column_strategy.value
        else:
            raise UnsupportedColumnStrategyError(column_strategy)

    def create_database(self):
        self.logger.warning("MSSQL: create_database ignored, database will be created when restore_db is run")

    def drop_database(self):
        # force connection close so we can always drop the db: sometimes timing makes a normal drop impossible.
        self.__execute(f"ALTER DATABASE [{self.db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        self.__execute(f"DROP DATABASE IF EXISTS [{self.db_name}];")

    def anonymize_database(self, database_strategy):
        qualifier_map = database_strategy.fake_update_qualifier_map

        if len(qualifier_map) > 0:
            self.logger.info("creating seed table with %d columns", len(qualifier_map))
            self.__create_seed_table(qualifier_map)

            self.logger.info("Inserting seed data")
            self.__seed(qualifier_map)

        self.__run_scripts(database_strategy.before_scripts, "before")

        table_strategies = database_strategy.table_strategies
        self.logger.info("Anonymizing %d tables", len(table_strategies))

        with tqdm(desc="Anonymizing database", total=len(table_strategies)) as progressbar:
            for table_strategy in table_strategies:
                table_name = table_strategy.table_name
                schema_prefix = f"[{table_strategy.schema}]." if table_strategy.schema else ""

                if table_strategy.strategy_type == TableStrategyTypes.TRUNCATE:
                    progressbar.set_description("Truncating {}".format(table_name))
                    self.__db_execute("TRUNCATE TABLE {}[{}];".format(schema_prefix, table_name))

                elif table_strategy.strategy_type == TableStrategyTypes.DELETE:
                    progressbar.set_description("Deleting {}".format(table_name))
                    self.__db_execute("DELETE FROM {}[{}];".format(schema_prefix, table_name))

                elif table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
                    progressbar.set_description("Anonymizing {}".format(table_name))
                    where_grouping = table_strategy.group_by_where()
                    total_wheres = len(where_grouping)

                    for i, (where, column_map) in enumerate(where_grouping.items()):
                        column_assignments = ",".join(["[{}] = {}".format(name, self.__get_column_subquery(column)) for name, column in column_map.items()])
                        where_clause = f" WHERE {where}" if where else ""
                        progressbar.set_description("Anonymizing {}: w[{}/{}]".format(table_name, i+1, total_wheres))
                        self.__db_execute("UPDATE {}[{}] SET {}{};".format(schema_prefix, table_name, column_assignments, where_clause))

                else:
                    raise UnsupportedTableStrategyError(table_strategy)

                progressbar.update()

        self.__run_scripts(database_strategy.after_scripts, "after")

        self.logger.info("Dropping seed table")
        self.__drop_seed_table()

    def restore_database(self, input_path):
        move_files = self.__get_file_moves(input_path)

        self.logger.info("Found %d files in %s", len(move_files), input_path )
        self.logger.debug(move_files)

        # get move statements and flatten pairs out so we can do the 2-param substitution
        move_clauses = ", ".join( ["MOVE ? TO ?"] * len(move_files) )
        move_clause_params = [item for pair in move_files.items() for item in pair]

        restore_cursor = self.__execute(f"RESTORE DATABASE ? FROM DISK = ? WITH {move_clauses}, STATS = ?;",
                                        [self.db_name, input_path, *move_clause_params, self.__STATS])

        self.__async_operation_progress("Restoring Database", restore_cursor)

    def dump_database(self, output_path):
        with_options = []
        if self.__backup_compression:
            with_options.append("COMPRESSION")

        with_options_str = ",".join(with_options) + ", " if len(with_options) > 0 else ""

        dump_cursor = self.__execute(f"BACKUP DATABASE ? TO DISK = ? WITH {with_options_str}STATS = ?;", [self.db_name, output_path, self.__STATS])
        self.__async_operation_progress("Dumping Database", dump_cursor)
