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
    parser = argparse.ArgumentParser(description="\n".join([
    "A tool for writing better anonymization strategies for your production databases.",
    ]))
    parser.add_argument("input", default=None, help="The source dumpfile to read from. \n[.sql, .gz]")
    parser.add_argument("strategyfile", default=None, help="A strategyfile to use during anonymization.")
    parser.add_argument("output", default=None, help="The destination to write the dumped output to. \n[.sql, .gz]")
    parser.add_argument("--db-type", "-t", default=None, help="database type.")
    parser.add_argument("--db-host", "-d", default=None, help="database host")
    parser.add_argument("--db-name", "-n", default=None, help="Name of database to create in the target host and restore to. This will default to a random name.")
    parser.add_argument("--db-user", "-u", default=None, help="Database username.")
    parser.add_argument("--db-password", "-p", default=None, help="Database password.")
    parser.add_argument("--fake-locale", "-l", default=None, help="locale to generate fake data for.")
    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser

def main(args=None):
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # find the dotenv from the current working dir rather than the execution location
    dotenv = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path=dotenv)

    input_path = parsed_args.input or os.getenv("PYNON_INPUT") or sys.exit("Missing argument: [input]/PYNON_INPUT")
    strategyfile_path = parsed_args.strategyfile or os.getenv("PYNON_STRATEGYFILE") or sys.exit("Missing argument: [strategyfile]/PYNON_STRATEGYFILE")
    output_path = parsed_args.output or os.getenv("PYNON_OUTPUT") or sys.exit("Missing argument: [output]/PYNON_OUTPUT")

    db_type = parsed_args.db_type or os.getenv("PYNON_DB_TYPE") or os.getenv("DB_TYPE") or "mysql"
    db_host = parsed_args.db_host or os.getenv("PYNON_DB_HOST") or os.getenv("DB_HOST") or "127.0.0.1"
    db_name = parsed_args.db_name or os.getenv("PYNON_DB_NAME") or os.getenv("DB_NAME") or get_temp_db_name(parsed_args.strategyfile)
    db_user = parsed_args.db_user or os.getenv("PYNON_DB_USER") or os.getenv("DB_USER") or sys.exit("Missing argument: --db-user/PYNON_DB_USER")
    db_pass = parsed_args.db_password or os.getenv("PYNON_DB_PASSWORD") or os.getenv("DB_PASS") or sys.exit("Missing argument: --db-password/PYNON_DB_PASSWORD")
    fake_locale = parsed_args.fake_locale or os.getenv("PYNON_FAKE_LOCALE") or os.getenv("FAKE_LOCALE") or "en_GB"

    fake_seeder = FakeColumnSet(fake_locale)
    strategy_parser = StrategyParser(fake_seeder)

    logger.debug("loading strategyfile %s", strategyfile_path)
    with open(strategyfile_path, "r") as strategy_yaml:
        strategy = strategy_parser.parse_config(yaml.safe_load(strategy_yaml))

    # init and validate DB connection
    logger.debug("Database: (%s)%s@%s db_name: %s", db_host, db_type, db_user, db_name)
    db = get_provider(db_type, db_host, db_user, db_pass, db_name)

    if not db.test_connection():
        sys.exit("Unable to connect to database.")

    # locate i/o
    input_obj = input.from_location(input_path)
    output_obj = output.from_location(output_path)
    logger.debug("input: %s output: %s", input_obj, output_obj)

    # main process
    logger.debug("Creating Database")
    db.create_database()

    logger.debug("Restoring Database")
    db.restore_database(input_obj)

    logger.debug("Anonymizing Database")
    db.anonymize_database(strategy)

    logger.debug("Dumping database")
    db.dump_database(output_obj)

    logger.debug("Dropping Database")
    db.drop_database()

    logger.info("Dumped anonymized data successfully.")

if __name__ == "__main__":
    main()
