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
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="\n".join([
    "A tool for writing better anonymization strategies for your production databases.",
    "",
    "environment variables:",
    "  DB_TYPE      Type of database (mysql)",
    "  DB_HOST      Database host/ip (127.0.0.1)",
    "  DB_USER      Database username",
    "  DB_PASS      Database password",
    "  FAKE_LOCALE  Locale to initialize faker generation (en_GB)",
    ]))
    parser.add_argument("input", help="The source dumpfile to read from. \n[.sql, .gz]")
    parser.add_argument("strategyfile", help="A strategyfile to use during anonymization.")
    parser.add_argument("output", help="The destination to write the dumped output to. \n[.sql, .gz]")
    parser.add_argument("--db-name", "-n", default=None, required=False, help="Name of database to create in the target host and restore to. This will default to a random name.")
    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser

def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args)

    # find the dotenv from the current working dir rather than the execution location
    dotenv = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path=dotenv)

    db_type = os.getenv("DB_TYPE") or "mysql"
    db_host = os.getenv("DB_HOST") or "127.0.0.1"
    db_user = os.getenv("DB_USER") or sys.exit("Missing environment variable: DB_USER")
    db_pass = os.getenv("DB_PASS") or sys.exit("Missing environment variable: DB_PASS")
    db_name = args.db_name or get_temp_db_name(args.strategyfile)
    fake_locale = os.getenv("FAKE_LOCALE") or "en_GB"

    fake_seeder = FakeColumnSet(fake_locale)
    strategy_parser = StrategyParser(fake_seeder)

    logger.debug("loading strategyfile %s", args.strategyfile)
    with open(args.strategyfile, "r") as strategy_yaml:
        strategy = strategy_parser.parse_config(yaml.safe_load(strategy_yaml))

    # init and validate DB connection
    logger.debug("Database: (%s)%s@%s db_name: %s", db_host, db_type, db_user, db_name)
    db = get_provider(db_type, db_host, db_user, db_pass, db_name)

    if not db.test_connection():
        sys.exit("Unable to connect to database.")

    # locate i/o
    input_obj = input.from_location(args.input)
    output_obj = output.from_location(args.output)
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
