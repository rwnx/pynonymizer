import subprocess
import shutil
from tqdm import tqdm
from datetime import date, datetime
from pynonymizer.database.exceptions import UnsupportedTableStrategyError, MissingPrerequisiteError, UnsupportedColumnStrategyError
from pynonymizer.strategy.table import TableStrategyTypes
from pynonymizer.strategy.update_column import ColumnStrategyTypes

from pynonymizer.log import get_logger


class MySqlQueryFactory:
    """
    Generates sql statements for MySqlProvider
    """
    @staticmethod
    def __get_column_subquery(seed_table_name, column_name, column_strategy):
        # For preservation of unique values across versions of mysql, and this bug:
        # https://bugs.mysql.com/bug.php?id=89474, use md5 based rand subqueries

        if column_strategy.strategy_type == ColumnStrategyTypes.EMPTY:
            return "('')"
        elif column_strategy.strategy_type == ColumnStrategyTypes.UNIQUE_EMAIL:
            return "( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '@', MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '.com') )"
        elif column_strategy.strategy_type == ColumnStrategyTypes.UNIQUE_LOGIN:
            return "( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())))) )"
        elif column_strategy.strategy_type == ColumnStrategyTypes.FAKE_UPDATE:
            return f"( SELECT `{column_strategy.fake_column.name}` FROM `{seed_table_name}` ORDER BY RAND() LIMIT 1)"
        else:
            raise UnsupportedColumnStrategyError(column_strategy)

    @staticmethod
    def __escape_sql_value(column):
        """
        return a sql-ified version of a seed column's value
        Normally this defines the stringification of datatypes and escaping for strings
        """
        value = column.get_value()
        if isinstance(value, (str, datetime, date)):
            return "'" + str(value).replace("'", "''") + "'"
        else:
            return str(value)

    @staticmethod
    def get_truncate_table(table_name):
        return f"SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE `{table_name}`; SET FOREIGN_KEY_CHECKS=1;"

    @staticmethod
    def get_create_seed_table(table_name, columns):
        if len(columns) < 1:
            raise ValueError("Cannot create a seed table with no columns")

        column_types = ",".join(map(lambda col: f"`{col.name}` {col.sql_type}", columns))
        return f"CREATE TABLE `{table_name}` ({column_types});"

    @staticmethod
    def get_drop_seed_table(table_name):
        return f"DROP TABLE IF EXISTS `{table_name}`;"

    @staticmethod
    def get_insert_seed_row(table_name, columns):
        column_names = ",".join(map(lambda col: f"`{col.name}`", columns))
        column_values = ",".join(map(lambda col: MySqlQueryFactory.__escape_sql_value(col), columns))

        return f"INSERT INTO `{table_name}`({column_names}) VALUES ({column_values});"

    @staticmethod
    def get_create_database(database_name):
        return f"CREATE DATABASE `{database_name}`;"

    @staticmethod
    def get_drop_database(database_name):
        return f"DROP DATABASE IF EXISTS `{database_name}`;"

    @staticmethod
    def get_update_table(seed_table_name, table_name, column_strategies):
        update_statements = []
        for column_name, column_strategy in column_strategies.items():
            update_statements.append(f"`{column_name}` = {MySqlQueryFactory.__get_column_subquery(seed_table_name, column_name, column_strategy)}")
        update_column_assignments = ",".join( update_statements )

        return f"UPDATE `{table_name}` SET {update_column_assignments};"

    @staticmethod
    def get_dumpsize_estimate(database_name):
        return f"SELECT data_bytes FROM (SELECT SUM(data_length) AS data_bytes FROM information_schema.tables WHERE table_schema = '{database_name}') AS data;"


class MySqlDumpRunner:
    def __init__(self, db_host, db_user, db_pass, db_name):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name

        if not (shutil.which("mysqldump")):
            raise MissingPrerequisiteError("The 'mysqldump' client must be present in the $PATH")

    def __get_base_params(self):
        return ["mysqldump", "--host", self.db_host, "--user", self.db_user, f"-p{self.db_pass}"]

    def open_dumper(self):
        return subprocess.Popen(self.__get_base_params() + [self.db_name], stdout=subprocess.PIPE)


class MySqlCmdRunner:
    def __init__(self, db_host, db_user, db_pass, db_name):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name

        if not (shutil.which("mysql")):
            raise MissingPrerequisiteError("The 'mysql' client must be present in the $PATH")

    def __get_base_params(self):
        return ["mysql", "-h", self.db_host, "-u", self.db_user, f"-p{self.db_pass}"]

    def execute(self, statement):
        return subprocess.check_output(self.__get_base_params() + ["--execute", statement])

    def db_execute(self, statement):
        return subprocess.check_output(self.__get_base_params() + [self.db_name,  "--execute", statement])

    def get_single_result(self, statement):
        return subprocess.check_output(self.__get_base_params() + ["-sN", self.db_name, "--execute", statement]).decode()

    def open_batch_processor(self):
        return subprocess.Popen(self.__get_base_params() + [self.db_name], stdin=subprocess.PIPE)


class MySqlProvider:
    """
    A command-line based mysql provider. Uses `mysql` and `mysqldump`,
    Because of the efficiency of piping mass amounts of sql into the command-line client.
    Unfortunately, this implementation provides limited feedback when things go wrong.
    """
    __SEED_TABLE_NAME = "_pynonymizer_seed_fake_data"
    __RESTORE_CHUNK_SIZE = 8192
    __DUMP_CHUNK_SIZE = 8192
    __DUMPSIZE_ESTIMATE_INFLATION = 1.15
    __sql = MySqlQueryFactory()
    logger = get_logger(__name__)

    def __init__(self, db_host, db_user, db_pass, db_name):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.__runner = MySqlCmdRunner(db_host, db_user, db_pass, db_name)
        self.__dumper = MySqlDumpRunner(db_host, db_user, db_pass, db_name)

    def __anonymize_table(self, table_name, table_strategy, progressbar):
        if table_strategy.strategy_type == TableStrategyTypes.TRUNCATE:
            progressbar.set_description("Truncating {}".format(table_name))
            self.__runner.db_execute(self.__sql.get_truncate_table(table_name))

        elif table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
            progressbar.set_description("Anonymizing {}".format(table_name))
            statement = self.__sql.get_update_table(self.__SEED_TABLE_NAME, table_name, table_strategy.column_strategies)
            self.__runner.db_execute(statement)

        else:
            raise UnsupportedTableStrategyError(table_strategy)

        progressbar.update()

    def __seed(self, columns, seed_rows=150):
        """
        'Seed' the database with a bunch of pre-generated random records so updates can be performed in batch updates
        """
        for i in tqdm(range(0, seed_rows), desc="Inserting seed data", unit="rows"):
            self.logger.debug(f"inserting seed row {i}")
            self.__runner.db_execute(self.__sql.get_insert_seed_row(self.__SEED_TABLE_NAME, columns))

    def __estimate_dumpsize(self):
        """
        Makes a guess on the dump size using internal database metrics
        :return:
        """
        statement = self.__sql.get_dumpsize_estimate(self.db_name)
        process_output = self.__runner.get_single_result(statement)

        return int(process_output) * self.__DUMPSIZE_ESTIMATE_INFLATION

    def __read_until_empty_byte(self, data):
        return iter(lambda: data.read(self.__RESTORE_CHUNK_SIZE), b'')

    def test_connection(self):
        """
        Prove a connection is viable - gives callers a fast-fail check for "did the client give me bad credentials?"
        Internally, execute some kind of easy NOOP that always works.
        :return True on success, False on Failure
        """
        try:
            self.__runner.execute("SELECT @@VERSION;")
            return True
        except subprocess.CalledProcessError:
            return False

    def create_database(self):
        """
        Create the working database
        :return:
        """
        self.__runner.execute(self.__sql.get_create_database(self.db_name))

    def drop_database(self):
        """
        Drop the working database
        :return:
        """
        self.__runner.execute(self.__sql.get_drop_database(self.db_name))

    def anonymize_database(self, database_strategy):
        """
        Anonymize a restored database using the passed database strategy
        :param database_strategy: a strategy.DatabaseStrategy configuration
        :return:
        """
        # Filter supported columns so we're not seeding ALL types by default
        required_columns = database_strategy.get_fake_columns()

        self.logger.info("creating seed table with %d columns", len(required_columns))
        self.__runner.db_execute(self.__sql.get_create_seed_table(self.__SEED_TABLE_NAME, required_columns))

        self.logger.info("inserting seed data")
        self.__seed(required_columns)

        table_strategies = database_strategy.table_strategies
        self.logger.info("Anonymizing %d tables", len(table_strategies))

        with tqdm(desc="Anonymizing database", total=len(table_strategies)) as progressbar:
            for table_name, table_strategy in table_strategies.items():
                self.__anonymize_table(table_name, table_strategy, progressbar)

        self.logger.info("dropping seed table")
        self.__runner.db_execute(self.__sql.get_drop_seed_table(self.__SEED_TABLE_NAME))

    def restore_database(self, input_obj):
        """
        Feed a mysqldump dumpfile to the mysql binary on stdin.
        :param input_obj:
        :return:
        """
        dumpsize = input_obj.get_size()

        batch_processor = self.__runner.open_batch_processor()
        with input_obj.open() as dumpfile_data:
            with tqdm(desc="Restoring", total=dumpsize, unit='B', unit_scale=True, unit_divisor=1000) as bar:
                for chunk in self.__read_until_empty_byte(dumpfile_data):
                    batch_processor.stdin.write(chunk)
                    batch_processor.stdin.flush()
                    bar.update(len(chunk))

    def dump_database(self, output_obj):
        """
        Feed an output with stdout from the mysqldump binary
        :param output_obj:
        :return:
        """
        dumpsize_estimate = self.__estimate_dumpsize()

        dump_process = self.__dumper.open_dumper()
        with output_obj.open() as output_file:
            with tqdm(desc="Dumping", total=dumpsize_estimate, unit='B', unit_scale=True, unit_divisor=1000) as bar:
                for chunk in self.__read_until_empty_byte(dump_process.stdout):
                    output_file.write(chunk)
                    bar.update(len(chunk))
