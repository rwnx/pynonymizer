import yaml
import argparse
from dotenv import load_dotenv
import os
import database
import fakedata
from strategy import DatabaseStrategy
import input
import output

if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()

    parser.add_argument("input_location")
    parser.add_argument("strategy")
    parser.add_argument("output_location")

    args = parser.parse_args()

    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")
    fake_locale = os.getenv("FAKE_LOCALE")

    fake_seeder = fakedata.FakeSeeder(fake_locale)

    strategy_file = os.path.join( "strategies", "{}.yml".format(args.strategy))
    with open(strategy_file, "r") as strategy_yaml:
        strategy = DatabaseStrategy( fake_seeder, yaml.safe_load( strategy_yaml ) )

    # init and validate DB connection
    db = database.get_provider("mysql", db_host, db_user, db_pass, db_name)

    # validate and locate i/o
    input = input.get_input(args.input_location)
    output = output.get_output(args.output_location)

    # main process
    db.create_database()
    db.restore_database(input)

    fake_seeder.seed(db, strategy)

    db.anonymize_database(strategy)
    db.drop_seed_table()
    db.dump_database(output)

    db.drop_database()
