import yaml
import argparse
from dotenv import load_dotenv, find_dotenv
import os
import sys
import textwrap
from pynonymizer.database import get_temp_db_name, get_provider
from pynonymizer.fake import FakeColumnSet
from pynonymizer.strategy.parser import StrategyParser
from pynonymizer import input
from pynonymizer import output
from pynonymizer.log import get_default_logger
from pynonymizer.version import __version__

logger = get_default_logger()


def create_parser():
    parser = argparse.ArgumentParser(description="A tool for writing better anonymization strategies for your production databases.")
    parser.add_argument("input",
                        default=os.getenv("PYNONYMIZER_INPUT"),
                        help="The source dumpfile to read from. \n[.sql, .gz]")

    parser.add_argument("strategyfile",
                        default=os.getenv("PYNONYMIZER_STRATEGYFILE"),
                        help="A strategyfile to use during anonymization.")

    parser.add_argument("output",
                        default=os.getenv("PYNONYMIZER_OUTPUT"),
                        help="The destination to write the dumped output to. \n[.sql, .gz]")

    parser.add_argument("--db-type", "-t",
                        default=os.getenv("DB_TYPE") ,
                        help="database type.")

    parser.add_argument("--db-host", "-d",
                        default=os.getenv("PYNONYMIZER_DB_HOST") or os.getenv("DB_HOST") or "127.0.0.1",
                        help="database host")

    parser.add_argument("--db-name", "-n",
                        default=os.getenv("PYNONYMIZER_DB_NAME") or os.getenv("DB_NAME"),
                        help="Name of database to create in the target host and restore to. This will default to a random name.")

    parser.add_argument("--db-user", "-u",
                        default=os.getenv("PYNONYMIZER_DB_USER") or os.getenv("DB_USER"),
                        help="Database username.")

    parser.add_argument("--db-password", "-p",
                        default=os.getenv("PYNONYMIZER_DB_PASSWORD") or os.getenv("DB_PASS"),
                        help="Database password.")

    parser.add_argument("--fake-locale", "-l",
                        default=os.getenv("PYNONYMIZER_OUTPUT"),
                        help="locale to generate fake data for.")

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser


def run(input_path, strategyfile_path, output_path, db_type, db_host, db_name, db_user, db_password, fake_locale):
    fake_seeder = FakeColumnSet(fake_locale)
    strategy_parser = StrategyParser(fake_seeder)

    logger.debug("loading strategyfile %s...", strategyfile_path)
    with open(strategyfile_path, "r") as strategy_yaml:
        strategy = strategy_parser.parse_config(yaml.safe_load(strategy_yaml))

    # init and validate DB connection
    logger.debug("Database: (%s)%s@%s db_name: %s", db_host, db_type, db_user, db_name)
    db_provider = get_provider(db_type, db_host, db_user, db_password, db_name)

    if not db_provider.test_connection():
        sys.exit("Unable to connect to database.")

    # locate i/o
    input_obj = input.from_location(input_path)
    output_obj = output.from_location(output_path)
    logger.debug("input: %s output: %s", input_obj, output_obj)

    # main process
    logger.debug("Creating Database")
    db_provider.create_database()

    logger.debug("Restoring Database")
    db_provider.restore_database(input_obj)

    logger.debug("Anonymizing Database")
    db_provider.anonymize_database(strategy)

    logger.debug("Dumping database")
    db_provider.dump_database(output_obj)

    logger.debug("Dropping Database")
    db_provider.drop_database()

    logger.info("Dumped anonymized data successfully.")

def main(rawAargs=None):
    """
    Main entry point for the command line. Parse the cmdargs, load env and call to the main process
    :param args:
    :return:
    """
    # find the dotenv from the current working dir rather than the execution location
    dotenv = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path=dotenv)

    parser = create_parser()
    args = parser.parse_args(rawAargs)

    run(
        args.input,
        args.strategyfile,
        args.db_type,
        args.db_host,
        args.db_name,
        args.db_user,
        args.db_password,
        args.fake_locale
    )


if __name__ == "__main__":
    main()
