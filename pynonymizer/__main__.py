import yaml
import argparse
from dotenv import load_dotenv, find_dotenv
import os
import sys
from pynonymizer import database
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
    parser.add_argument("input_location", help="The source dumpfile to read from")
    parser.add_argument("strategyfile", help="a strategyfile to use during anonymization (e.g. example.yml)")
    parser.add_argument("output_location", help="The destination to write the output to")

    args = parser.parse_args()

    db_host = os.getenv("DB_HOST") or "127.0.0.1"
    db_user = os.getenv("DB_USER") or sys.exit("Missing environment variable: DB_USER")
    db_pass = os.getenv("DB_PASS") or sys.exit("Missing environment variable: DB_PASS")
    db_name = os.getenv("DB_NAME") or sys.exit("Missing environment variable: DB_NAME")
    fake_locale = os.getenv("FAKE_LOCALE") or "en_GB"

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
