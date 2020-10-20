from pynonymizer.database.provider import SEED_TABLE_NAME
from tqdm import tqdm
from pynonymizer import log
from pynonymizer.database.provider import DatabaseProvider
from pynonymizer.database.exceptions import UnsupportedTableStrategyError
from pynonymizer.database.postgres import execution, query_factory
from pynonymizer.database.basic.input import resolve_input
from pynonymizer.database.basic.output import resolve_output
from pynonymizer.strategy.table import TableStrategyTypes


class PostgreSqlProvider(DatabaseProvider):
    """
    A command-line based postgres provider. Uses `psql` and `psqldump`,
    Because of the efficiency of piping mass amounts of sql into the command-line client.
    Unfortunately, this implementation provides limited feedback when things go wrong.
    """
    __CHUNK_SIZE = 8192
    logger = log.get_logger(__name__)

    def __init__(self, db_host, db_user, db_pass, db_name, db_port=None, seed_rows=None):
        if db_port is None:
            db_port = "5432"
        if db_host is None:
            db_host = "127.0.0.1"
        super().__init__(db_host=db_host, db_user=db_user, db_pass=db_pass, db_name=db_name, db_port=db_port, seed_rows=seed_rows)
        self.__runner = execution.PSqlCmdRunner(db_host=db_host, db_user=db_user, db_pass=db_pass, db_name=db_name, db_port=db_port)
        self.__dumper = execution.PSqlDumpRunner(db_host=db_host, db_user=db_user, db_pass=db_pass, db_name=db_name, db_port=db_port)

    def __seed(self, qualifier_map):
        """
        'Seed' the database with a bunch of pre-generated random records so updates can be performed in batch updates
        """
        for i in tqdm(range(0, self.seed_rows), desc="Inserting seed data", unit="rows"):
            self.logger.debug(f"Inserting seed row {i}")
            self.__runner.db_execute(query_factory.get_insert_seed_row(SEED_TABLE_NAME, qualifier_map))

    def __estimate_dumpsize(self):
        """
        Makes a guess on the dump size using internal database metrics
        :return: A value in bytes, or None (unknown)
        """
        statement = query_factory.get_dumpsize_estimate(self.db_name)
        process_output = self.__runner.get_single_result(statement)

        try:
            return int(process_output)
        except ValueError:
            # Value unparsable, likely NULL
            return None

    def __read_until_empty_byte(self, data):
        return iter(lambda: data.read(self.__CHUNK_SIZE), b'')

    def __run_scripts(self, script_list, title=""):
        for i, script in enumerate(script_list):
            self.logger.info(f"Running f{title} script #{i} \"{script[:50]}\"")
            self.logger.info(self.__runner.db_execute(script))

    def create_database(self):
        """Create the working database"""
        self.__runner.execute(query_factory.get_create_database(self.db_name))

    def drop_database(self):
        """Drop the working database"""
        self.__runner.execute(query_factory.get_drop_database(self.db_name))

    def anonymize_database(self, database_strategy):
        """
        Anonymize a restored database using the passed database strategy
        :param database_strategy: a strategy.DatabaseStrategy configuration
        :return:
        """
        qualifier_map = database_strategy.fake_update_qualifier_map

        if len(qualifier_map) > 0:
            self.logger.info("creating seed table with %d columns", len(qualifier_map))
            create_seed_table_sql = query_factory.get_create_seed_table(SEED_TABLE_NAME, qualifier_map)
            self.__runner.db_execute(create_seed_table_sql)

            self.logger.info("Inserting seed data")
            self.__seed(qualifier_map)

        self.__run_scripts(database_strategy.before_scripts, "before")

        table_strategies = database_strategy.table_strategies
        self.logger.info("Anonymizing %d tables", len(table_strategies))

        with tqdm(desc="Anonymizing database", total=len(table_strategies)) as progressbar:
            for table_strategy in table_strategies:
                if table_strategy.strategy_type == TableStrategyTypes.TRUNCATE:
                    progressbar.set_description("Truncating {}".format(table_strategy.qualified_name))
                    self.__runner.db_execute(query_factory.get_truncate_table(table_strategy))

                elif table_strategy.strategy_type == TableStrategyTypes.DELETE:
                    progressbar.set_description("Deleting {}".format(table_strategy.qualified_name))
                    self.__runner.db_execute(query_factory.get_delete_table(table_strategy))

                elif table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
                    progressbar.set_description("Anonymizing {}".format(table_strategy.qualified_name))
                    statements = query_factory.get_update_table(SEED_TABLE_NAME, table_strategy)
                    self.__runner.db_execute(statements)

                else:
                    raise UnsupportedTableStrategyError(table_strategy)

                progressbar.update()

        self.__run_scripts(database_strategy.after_scripts, "after")

        self.logger.info("dropping seed table")
        self.__runner.db_execute(query_factory.get_drop_seed_table(SEED_TABLE_NAME))

    def restore_database(self, input_path):
        """
        Feed a mysqldump dumpfile to the mysql binary on stdin.
        :param input_path:
        :return:
        """
        input_obj = resolve_input(input_path)
        dumpsize = input_obj.get_size()

        batch_processor = self.__runner.open_batch_processor()
        with input_obj.open() as dumpfile_data:
            with tqdm(desc="Restoring", total=dumpsize, unit='B', unit_scale=True, unit_divisor=1000) as bar:
                for chunk in self.__read_until_empty_byte(dumpfile_data):
                    batch_processor.write(chunk)
                    batch_processor.flush()
                    bar.update(len(chunk))

    def dump_database(self, output_path):
        """
        Feed an output with stdout from the dump binary
        :param output_path:
        :return:
        """
        output_obj = resolve_output(output_path)
        dumpsize_estimate = self.__estimate_dumpsize()

        dump_process = self.__dumper.open_dumper()
        with output_obj.open() as output_file:
            with tqdm(desc="Dumping", total=dumpsize_estimate, unit='B', unit_scale=True, unit_divisor=1000) as bar:
                for chunk in self.__read_until_empty_byte(dump_process):
                    output_file.write(chunk)
                    bar.update(len(chunk))
