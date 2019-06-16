import subprocess
from tqdm import tqdm
from pynonymizer.database.exceptions import UnsupportedTableStrategyError
from pynonymizer.strategy.table import TableStrategyTypes
import pynonymizer.database.mysql.query_factory as query_factory
import pynonymizer.database.mysql.execution as execution

from pynonymizer import log

class MySqlProvider:
    """
    A command-line based mysql provider. Uses `mysql` and `mysqldump`,
    Because of the efficiency of piping mass amounts of sql into the command-line client.
    Unfortunately, this implementation provides limited feedback when things go wrong.
    """
    __SEED_TABLE_NAME = "_pynonymizer_seed_fake_data"
    __CHUNK_SIZE = 8192
    __DUMPSIZE_ESTIMATE_INFLATION = 1.15
    logger = log.get_logger(__name__)

    def __init__(self, db_host, db_user, db_pass, db_name):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.__runner = execution.MySqlCmdRunner(db_host, db_user, db_pass, db_name)
        self.__dumper = execution.MySqlDumpRunner(db_host, db_user, db_pass, db_name)

    def __anonymize_table(self, table_name, table_strategy, progressbar):
        if table_strategy.strategy_type == TableStrategyTypes.TRUNCATE:
            progressbar.set_description("Truncating {}".format(table_name))
            self.__runner.db_execute(query_factory.get_truncate_table(table_name))

        elif table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
            progressbar.set_description("Anonymizing {}".format(table_name))
            statement = query_factory.get_update_table(self.__SEED_TABLE_NAME, table_name, table_strategy.column_strategies)
            self.__runner.db_execute(statement)

        else:
            raise UnsupportedTableStrategyError(table_strategy)

        progressbar.update()

    def __seed(self, columns, seed_rows=150):
        """
        'Seed' the database with a bunch of pre-generated random records so updates can be performed in batch updates
        """
        for i in tqdm(range(0, seed_rows), desc="Inserting seed data", unit="rows"):
            self.logger.debug(f"Inserting seed row {i}")
            self.__runner.db_execute(query_factory.get_insert_seed_row(self.__SEED_TABLE_NAME, columns))

    def __estimate_dumpsize(self):
        """
        Makes a guess on the dump size using internal database metrics
        :return: A value in bytes, or None (unknown)
        """
        statement = query_factory.get_dumpsize_estimate(self.db_name)
        process_output = self.__runner.get_single_result(statement)

        try:
            return int(process_output) * self.__DUMPSIZE_ESTIMATE_INFLATION
        except ValueError:
            # Value unparsable, likely NULL
            return None

    def __read_until_empty_byte(self, data):
        return iter(lambda: data.read(self.__CHUNK_SIZE), b'')

    def test_connection(self):
        return self.__runner.test()

    def create_database(self):
        """
        Create the working database
        :return:
        """
        self.__runner.execute(query_factory.get_create_database(self.db_name))

    def drop_database(self):
        """
        Drop the working database
        :return:
        """
        self.__runner.execute(query_factory.get_drop_database(self.db_name))

    def anonymize_database(self, database_strategy):
        """
        Anonymize a restored database using the passed database strategy
        :param database_strategy: a strategy.DatabaseStrategy configuration
        :return:
        """
        # Filter supported columns so we're not seeding ALL types by default
        required_columns = database_strategy.get_fake_columns()

        self.logger.info("creating seed table with %d columns", len(required_columns))
        self.__runner.db_execute(query_factory.get_create_seed_table(self.__SEED_TABLE_NAME, required_columns))

        self.logger.info("Inserting seed data")
        self.__seed(required_columns)

        try:
            for i, before_script in enumerate(database_strategy.scripts["before"]):
                self.logger.info(f"Running before script {i} \"{before_script[:50]}\"")
                self.logger.info( self.__runner.db_execute(before_script).decode() )
        except KeyError:
            pass

        table_strategies = database_strategy.table_strategies
        self.logger.info("Anonymizing %d tables", len(table_strategies))

        with tqdm(desc="Anonymizing database", total=len(table_strategies)) as progressbar:
            for table_name, table_strategy in table_strategies.items():
                self.__anonymize_table(table_name, table_strategy, progressbar)

        try:
            for i, after_script in enumerate(database_strategy.scripts["after"]):
                self.logger.info(f"Running after script {i}: \"{after_script[:50]}\"")
                self.logger.info( self.__runner.db_execute(after_script).decode() )
        except KeyError:
            pass

        self.logger.info("dropping seed table")
        self.__runner.db_execute(query_factory.get_drop_seed_table(self.__SEED_TABLE_NAME))

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
                    batch_processor.write(chunk)
                    batch_processor.flush()
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
                for chunk in self.__read_until_empty_byte(dump_process):
                    output_file.write(chunk)
                    bar.update(len(chunk))
