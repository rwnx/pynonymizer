from concurrent.futures import ThreadPoolExecutor
from time import sleep
import logging

from pynonymizer.database.io import dump, restore
from pynonymizer.database.provider import SEED_TABLE_NAME
from pynonymizer.database.exceptions import UnsupportedTableStrategyError
from pynonymizer.database.mysql import execution, query_factory
from pynonymizer.strategy.table import TableStrategy, TableStrategyTypes

logger = logging.getLogger(__name__)


class MySqlProvider:
    """
    A command-line based mysql provider. Uses `mysql` and `mysqldump`,
    Because of the efficiency of piping mass amounts of sql into the command-line client.
    Unfortunately, this implementation provides limited feedback when things go wrong.
    """

    __DUMPSIZE_ESTIMATE_INFLATION = 1.15

    def __init__(
        self,
        db_host,
        db_user,
        db_pass,
        db_name,
        seed_rows,
        progress,
        db_port=None,
        cmd_opts=None,
        dump_opts=None,
    ):
        if db_host is None:
            db_host = "127.0.0.1"
        if db_port is None:
            db_port = "3306"
        if cmd_opts is None:
            cmd_opts = ""
        if dump_opts is None:
            dump_opts = ""

        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port
        self.progress = progress

        self.seed_rows = int(seed_rows)

        self.__runner = execution.MySqlCmdRunner(
            db_host, db_user, db_pass, db_name, db_port, additional_opts=cmd_opts
        )
        self.__dumper = execution.MySqlDumpRunner(
            db_host, db_user, db_pass, db_name, db_port, additional_opts=dump_opts
        )

    def __seed(self, qualifier_map):
        """
        'Seed' the database with a bunch of pre-generated random records so updates can be performed in batch updates
        """
        for i in self.progress(
            range(0, self.seed_rows), desc="Inserting seed data", unit="rows"
        ):
            logger.debug(f"Inserting seed row {i}")
            self.__runner.db_execute(
                query_factory.get_insert_seed_row(SEED_TABLE_NAME, qualifier_map)
            )

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

    def __run_scripts(self, script_list, title=""):
        for i, script in enumerate(script_list):
            logger.info(f'Running {title} script #{i} "{script[:50]}"')
            logger.info(self.__runner.db_execute(script))

    def create_database(self):
        """Create the working database"""
        self.__runner.execute(query_factory.get_create_database(self.db_name))

    def drop_database(self):
        """Drop the working database"""
        self.__runner.execute(query_factory.get_drop_database(self.db_name))

    def anonymize_database(self, database_strategy, db_workers):
        """
        Anonymize a restored database using the passed database strategy
        :param database_strategy: a strategy.DatabaseStrategy configuration
        :return:
        """
        qualifier_map = database_strategy.fake_update_qualifier_map

        if len(qualifier_map) > 0:
            logger.info("creating seed table with %d columns", len(qualifier_map))
            create_seed_table_sql = query_factory.get_create_seed_table(
                SEED_TABLE_NAME, qualifier_map
            )
            self.__runner.db_execute(create_seed_table_sql)

            logger.info("Inserting seed data")
            self.__seed(qualifier_map)

        self.__run_scripts(database_strategy.before_scripts, "before")

        table_strategies = database_strategy.table_strategies
        logger.info("Anonymizing %d tables", len(table_strategies))

        anonymization_errors = []

        def anonymize_table(progressbar, table_strategy: TableStrategy):
            try:
                if table_strategy.schema is not None:
                    logger.warning(
                        "%s: MySQL provider does not support table schema. This option will be ignored.",
                        table_strategy.table_name,
                    )

                if table_strategy.strategy_type == TableStrategyTypes.TRUNCATE:
                    progressbar.set_description(
                        "Truncating {}".format(table_strategy.table_name)
                    )
                    self.__runner.db_execute(
                        query_factory.get_truncate_table(table_strategy.table_name)
                    )

                elif table_strategy.strategy_type == TableStrategyTypes.DELETE:
                    progressbar.set_description(
                        "Deleting {}".format(table_strategy.table_name)
                    )
                    self.__runner.db_execute(
                        query_factory.get_delete_table(table_strategy.table_name)
                    )

                elif table_strategy.strategy_type == TableStrategyTypes.UPDATE_COLUMNS:
                    progressbar.set_description(
                        "Anonymizing {}".format(table_strategy.table_name)
                    )
                    statements = query_factory.get_update_table(
                        SEED_TABLE_NAME, table_strategy
                    )
                    self.__runner.db_execute(statements)

                else:
                    raise UnsupportedTableStrategyError(table_strategy)
            except Exception as e:
                anonymization_errors.append(e)
                logger.exception(
                    f"Error while anonymizing table {table_strategy.qualified_name}"
                )

            progressbar.update()

        with self.progress(
            desc="Anonymizing database", total=len(table_strategies)
        ) as progressbar:
            with ThreadPoolExecutor(max_workers=db_workers) as e:
                for table_strategy in table_strategies:
                    e.submit(anonymize_table, progressbar, table_strategy)

        if len(anonymization_errors) > 0:
            raise Exception("Error during anonymization" + repr(anonymization_errors))

        self.__run_scripts(database_strategy.after_scripts, "after")

        logger.info("dropping seed table")
        self.__runner.db_execute(query_factory.get_drop_seed_table(SEED_TABLE_NAME))

        # Wait an arbitrary amount of time here to prevent this step from interacting with
        # transactional dump operations
        logger.debug("Waiting for trailing operations to complete...")
        sleep(0.2)

    def restore_database(self, input_path):
        try:
            restore_pipe = self.__runner.open()
            restore(self.progress, input_path, restore_pipe)
        finally:
            self.__runner.close()

    def dump_database(self, output_path):
        try:
            dump_stream = self.__dumper.open()
            dump(self.progress, output_path, dump_stream, self.__estimate_dumpsize())
        finally:
            self.__dumper.close()
