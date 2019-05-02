import yaml
import argparse
from dotenv import load_dotenv, find_dotenv
import os
import sys
from pynonymizer.database import get_temp_db_name, get_provider
from pynonymizer.fake import FakeSeeder
from pynonymizer.strategy.parser import StrategyParser
from pynonymizer.input import get_input
from pynonymizer.output import get_output
from pynonymizer.log import get_logger, get_default_logger

logger = get_default_logger()


def main(args=None):
    if sys.version_info < (3, 6):
        sys.exit('pynonymizer requires Python 3.6+ to run')

    # find the dotenv from the current working dir rather than the execution location
    dotenv = find_dotenv(usecwd=True)
    load_dotenv( dotenv_path=find_dotenv(usecwd=True) )

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="The source dumpfile to read from")
    parser.add_argument("strategyfile", help="a strategyfile to use during anonymization (e.g. example.yml)")
    parser.add_argument("output", help="The destination to write the output to")
    parser.add_argument("--db-name", "-n", default=None, required=False, help="Name of database to create/restore to")

    args = parser.parse_args()

    db_type = os.getenv("DB_TYPE") or "mysql"
    db_host = os.getenv("DB_HOST") or "127.0.0.1"
    db_user = os.getenv("DB_USER") or sys.exit("Missing environment variable: DB_USER")
    db_pass = os.getenv("DB_PASS") or sys.exit("Missing environment variable: DB_PASS")
    db_name = args.db_name or get_temp_db_name(args.strategyfile)
    fake_locale = os.getenv("FAKE_LOCALE") or "en_GB"

    fake_seeder = FakeSeeder(fake_locale)
    strategy_parser = StrategyParser(fake_seeder)

    logger.debug("loading strategyfile %s", args.strategyfile)
    with open(args.strategyfile, "r") as strategy_yaml:
        strategy = strategy_parser.parse_config(yaml.safe_load(strategy_yaml))

    # init and validate DB connection
    logger.debug("Connecting to database: (%s)%s user: %s db_name: %s", db_host, db_type, db_user, db_name)
    db = get_provider(db_type, db_host, db_user, db_pass, db_name)

    # validate and locate i/o
    input = get_input(args.input)
    output = get_output(args.output)
    logger.debug("input: %s output: %s", input, output)

    # main process
    logger.debug("Creating Database")
    db.create_database()

    logger.debug("Restoring Database")
    db.restore_database(input)

    logger.debug("Anonymizing Database")
    db.anonymize_database(fake_seeder, strategy)

    logger.debug("Dumping database")
    db.dump_database(output)

    logger.debug("Dropping Database")
    db.drop_database()

    logger.info("Dumped anonymized data successfully.")

if __name__ == "__main__":
    main()
