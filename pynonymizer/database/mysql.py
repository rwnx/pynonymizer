import subprocess
import shutil
from tqdm import tqdm
from datetime import date, datetime
from pynonymizer.database.exceptions import UnsupportedTableStrategyError, DatabaseConnectionError, MissingPrerequisiteError, UnsupportedColumnStrategyError
from pynonymizer.strategy.table import TableStrategyTypes
from pynonymizer.strategy.update_column import ColumnStrategyTypes

from pynonymizer.log import get_logger
logger = get_logger(__name__)

class MySqlProvider:
    """
    A command-line based mysql provider. Uses `mysql` and `mysqldump`
    Because of the efficiency of piping mass amounts of sql into the command-line client, this was selected over a native python lib
    """
    SEED_TABLE_NAME = "_pynonymizer_seed_fake_data"
    RESTORE_CHUNK_SIZE = 8192
    DUMP_CHUNK_SIZE = 8192
    DUMPSIZE_ESTIMATE_INFLATION = 1.13

    def __init__(self, db_host, db_user, db_pass, db_name):
        if not (shutil.which("mysql") and shutil.which("mysqldump")):
            raise MissingPrerequisiteError("This provider requires mysql and mysqldump tools in $PATH to run. Verify these are installed.")

        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        # test connection
        try:
            version = self.__execute_statement("SELECT @@VERSION;", "-sN").decode()
            logger.info(f"mysql version {version}")
        except subprocess.CalledProcessError as error:
            raise DatabaseConnectionError() from None

    def __execute_statement(self, statement, *args):
        return subprocess.check_output(["mysql", "-h", self.db_host, "-u", self.db_user, f"-p{self.db_pass}", *args, "--execute", statement])

    def __execute_db_statement(self, statement, *args):
        return subprocess.check_output(["mysql", "-h", self.db_host, "-u", self.db_user, f"-p{self.db_pass}", *args, self.db_name,  "--execute", statement])

    def __get_seed_sql_value(self, column):
        """
        return a sql-ified version of a seed column's value
        Normally this defines the stringification of datatypes and escaping for strings
        :param column:
        :return:
        """
        value = column.get_value()
        if isinstance(value, (str, datetime, date)):
            return "'" + str(value).replace("'", "''") + "'"
        else:
            return str(value)

    def __truncate_table(self, table_name):
        self.__execute_db_statement(f"SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE `{table_name}`; SET FOREIGN_KEY_CHECKS=1;")

    def __get_column_subquery(self, column_name, column_strategy):
        # For preservation of unique values across versions of mysql, and this bug:
        # https://bugs.mysql.com/bug.php?id=89474,

        if column_strategy.strategy_type == ColumnStrategyTypes.EMPTY:
            return "('')"
        elif column_strategy.strategy_type == ColumnStrategyTypes.UNIQUE_EMAIL:
            return "( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '@', MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '.com') )"
        elif column_strategy.strategy_type == ColumnStrategyTypes.UNIQUE_LOGIN:
            return "( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())))) )"
        elif column_strategy.strategy_type == ColumnStrategyTypes.FAKE_UPDATE:
            return f"( SELECT `{column_strategy.fake_column.name}` FROM `{self.SEED_TABLE_NAME}` ORDER BY RAND() LIMIT 1)"
        else:
            raise UnsupportedColumnStrategyError(column_strategy)

    def __update_table_columns(self, table_name, table_strategy):
        column_strategies = table_strategy.column_strategies
        update_column_assignments = ",".join( f"`{column_name}` = {self.__get_column_subquery(column_name, column_strategy)}" for column_name, column_strategy in column_strategies.items() )

        self.__execute_db_statement(f"UPDATE `{table_name}` SET {update_column_assignments};" )

    def __anonymize_table(self, table_name, table_strategy, progressbar):
        if table_strategy.strategy_type == TableStrategyTypes.TRUNCATE:
            progressbar.set_description("Truncating {}".format(table_name))
            self.__truncate_table(table_name)

        elif table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
            progressbar.set_description("Anonymizing {}".format(table_name))
            self.__update_table_columns(table_name, table_strategy)

        else:
            raise UnsupportedTableStrategyError(table_strategy)

        progressbar.update()


    def __seed(self, columns, seed_rows=150):
        """
        'Seed' the database with a bunch of pre-generated random records so updates can be performed in batch updates
        """
        for i in tqdm(range(0, seed_rows), desc="Inserting seed data", unit="rows"):
            logger.debug(f"inserting seed row {i}")
            self.__insert_seed_row(columns)

    def __create_seed_table(self, columns):
        if len(columns) < 1:
            raise ValueError("Cannot create a seed table with no columns")

        column_types = ",".join(map(lambda col: f"`{col.name}` {col.sql_type}", columns))
        self.__execute_db_statement(f"CREATE TABLE `{self.SEED_TABLE_NAME}` ({column_types});")

    def __drop_seed_table(self):
        self.__execute_db_statement(f"DROP TABLE IF EXISTS `{self.SEED_TABLE_NAME}`;")

    def __insert_seed_row(self, columns):
        column_names = ",".join(map(lambda col: f"`{col.name}`", columns))
        column_values = ",".join(map(lambda col: self.__get_seed_sql_value(col), columns))
        self.__execute_db_statement(f"INSERT INTO `{self.SEED_TABLE_NAME}`({column_names}) VALUES ({column_values});")

    def __estimate_dumpsize(self):
        """
        Makes a guess on the dump size using internal database metrics
        :return:
        """
        statement = f"SELECT data_bytes FROM (SELECT SUM(data_length) AS data_bytes FROM information_schema.tables WHERE table_schema = '{self.db_name}') AS data;"
        process_output = subprocess.check_output(
            ["mysql", "-h", self.db_host, "-u", self.db_user, "-p{}".format(self.db_pass), self.db_name, "-sN",
             "--execute", statement])

        return int(process_output.decode()) * self.DUMPSIZE_ESTIMATE_INFLATION

    def anonymize_database(self, database_strategy):
        """
        Anonymize a restored database using the passed database strategy

        :param database_strategy: a strategy.DatabaseStrategy configuration
        :return:
        """
        # Filter supported columns so we're not seeding ALL types by default
        required_columns = database_strategy.get_fake_columns()

        logger.info("creating seed table with %d columns", len(required_columns))
        self.__create_seed_table(required_columns)

        logger.info("inserting seed data")
        self.__seed(required_columns)

        table_strategies = database_strategy.table_strategies
        logger.info("Anonymizing %d tables", len(table_strategies))

        with tqdm(desc="Anonymizing database", total=len(table_strategies)) as progressbar:
            for table_name, table_strategy in table_strategies.items():
                self.__anonymize_table(table_name, table_strategy, progressbar)

        logger.info("dropping seed table")
        self.__drop_seed_table()

    def create_database(self):
        self.__execute_statement(f"CREATE DATABASE `{self.db_name}`;")

    def drop_database(self):
        self.__execute_statement(f"DROP DATABASE IF EXISTS `{self.db_name}`;")

    def restore_database(self, input):
        """
        Feed a mysqldump dumpfile to the mysql binary on stdin.
        :param input:
        :return:
        """
        dumpsize = input.get_size()

        restore_process = subprocess.Popen(
            ["mysql", "--host", self.db_host, "--user", self.db_user, f"-p{self.db_pass}", self.db_name],
            stdin=subprocess.PIPE)
        with input.open() as dumpfile_data:
            with tqdm(desc="Restoring database", total=dumpsize, unit='B', unit_scale=True,
                      unit_divisor=1000) as progressbar:
                for chunk in iter(lambda: dumpfile_data.read(self.RESTORE_CHUNK_SIZE), b''):
                    restore_process.stdin.write(chunk)
                    restore_process.stdin.flush()
                    progressbar.update(len(chunk))

    def dump_database(self, output):
        """
        Feed an output with stdout from the mysqldump binary
        :param output:
        :return:
        """
        dumpsize_estimate = self.__estimate_dumpsize()

        with output.open() as output_file:
            dump_process = subprocess.Popen(["mysqldump", "--host", self.db_host, "--user", self.db_user, f"-p{self.db_pass}", self.db_name], stdout=subprocess.PIPE)
            with tqdm(desc="Dumping database", total=dumpsize_estimate, unit='B', unit_scale=True, unit_divisor=1000) as progressbar:
                for chunk in iter(lambda: dump_process.stdout.read(self.DUMP_CHUNK_SIZE), b''):
                    output_file.write(chunk)
                    progressbar.update(len(chunk))

