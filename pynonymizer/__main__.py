import yaml
import argparse
from dotenv import load_dotenv
import os
import sys
from pynonymizer import database
from pynonymizer.faker import FakeSeeder
from pynonymizer.strategy.parser import StrategyParser
from pynonymizer.input import get_input
from pynonymizer.output import get_output
from pynonymizer.logging import get_logger, get_default_logger

logger = get_default_logger()

def main(args=None):
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_location", help="The source dumpfile to read from")
    parser.add_argument("strategyfile", help="a strategyfile to use during anonymization (e.g. example.yml)")
    parser.add_argument("output_location", help="The destination to write the output to")

    args = parser.parse_args()


    db_host = os.getenv("DB_HOST") or "127.0.0.1"
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")
    fake_locale = os.getenv("FAKE_LOCALE") or "en_GB"
    env_type = os.getenv("ENV_TYPE") or "development"

    # Validate required env
    if db_user is None:
        logger.error("Missing required environment variable: %s", "DB_USER")
        sys.exit(1)

    if db_pass is None:
        logger.error("Missing required environment variable: %s", "DB_PASS")
        sys.exit(1)

    if db_name is None:
        logger.error("Missing required environment variable: %s", "DB_NAME")
        sys.exit(1)

    if env_type == "production":
        sys.tracebacklimit  = 0

    fake_seeder = FakeSeeder(fake_locale)
    strategy_parser = StrategyParser()

    with open(args.strategyfile, "r") as strategy_yaml:
        strategy = strategy_parser.parse_config(yaml.safe_load(strategy_yaml))

    # init and validate DB connection
    db = database.get_provider("mysql", db_host, db_user, db_pass, db_name)

    # validate and locate i/o
    input = get_input(args.input_location)
    output = get_output(args.output_location)

    # main process
    db.create_database()
    db.restore_database(input)

    fake_seeder.seed(db, strategy)

    db.anonymize_database(strategy)
    db.drop_seed_table()
    db.dump_database(output)

    db.drop_database()
    logger.info("Process completed successfully")


if __name__ == "__main__":
    main()
