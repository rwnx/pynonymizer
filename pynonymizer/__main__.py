import yaml
import argparse
import dotenv
import os
import sys
from pynonymizer.database import get_temp_db_name, get_provider
from pynonymizer.fake import FakeColumnSet
from pynonymizer.strategy.parser import StrategyParser
from pynonymizer import input
from pynonymizer import output
from pynonymizer.log import get_default_logger
from pynonymizer.version import __version__

logger = get_default_logger()


class ArgumentValidationError(Exception):
    def __init__(self, validation_messages):
        self.validation_messages = validation_messages


class DatabaseConnectionError(Exception):
    pass


def create_parser():
    parser = argparse.ArgumentParser(prog="pynonymizer", description="A tool for writing better anonymization strategies for your production databases.")
    input_positional = parser.add_mutually_exclusive_group(required=False)
    input_positional.add_argument("legacy_input",
                        nargs="?",
                        help=argparse.SUPPRESS)

    strategy_positional = parser.add_mutually_exclusive_group(required=False)
    strategy_positional.add_argument("legacy_strategyfile",
                        nargs="?",
                        help=argparse.SUPPRESS)

    output_positional = parser.add_mutually_exclusive_group(required=False)
    output_positional.add_argument("legacy_output",
                        nargs="?",
                        help=argparse.SUPPRESS)

    input_positional.add_argument("--input", "-i",
                        default=os.getenv("PYNONYMIZER_INPUT"),
                        help="The source dumpfile to read from. [file.sql, file.sql.gz] [$PYNONYMIZER_INPUT]")

    strategy_positional.add_argument("--strategy", "-s",
                        dest="strategyfile",
                        default=os.getenv("PYNONYMIZER_STRATEGY"),
                        help="A strategyfile to use during anonymization. [$PYNONYMIZER_STRATEGY]")

    output_positional.add_argument("--output", "-o",
                        default=os.getenv("PYNONYMIZER_OUTPUT"),
                        help="The destination to write the dumped output to. [file.sql, file.sql.gz] [$PYNONYMIZER_OUTPUT]")

    parser.add_argument("--db-type", "-t",
                        default=os.getenv("PYNONYMIZER_DB_TYPE") or os.getenv("DB_TYPE"),
                        help="Type of database to interact with. More databases will be supposed in future versions. default: mysql [$PYNONYMIZER_DB_TYPE]")

    parser.add_argument("--db-host", "-d",
                        default=os.getenv("PYNONYMIZER_DB_HOST") or os.getenv("DB_HOST"),
                        help="Database hostname or IP address. [$PYNONYMIZER_DB_HOST]")

    parser.add_argument("--db-name", "-n",
                        default=os.getenv("PYNONYMIZER_DB_NAME") or os.getenv("DB_NAME"),
                        help="Name of database to restore and anonymize in. If not provided, a unique name will be generated from the strategy name. This will be dropped at the end of the run. [$PYNONYMIZER_DB_NAME]")

    parser.add_argument("--db-user", "-u",
                        default=os.getenv("PYNONYMIZER_DB_USER") or os.getenv("DB_USER"),
                        help="Database credentials: username. [$PYNONYMIZER_DB_USER]")

    parser.add_argument("--db-password", "-p",
                        default=os.getenv("PYNONYMIZER_DB_PASSWORD") or os.getenv("DB_PASS"),
                        help="Database credentials: password. Recommended: use environment variables to avoid exposing secrets in production environments. [$PYNONYMIZER_DB_PASSWORD]")

    parser.add_argument("--fake-locale", "-l",
                        default=os.getenv("PYNONYMIZER_FAKE_LOCALE") or os.getenv("FAKE_LOCALE"),
                        help="Locale setting to initialize fake data generation. Affects Names, addresses, formats, etc. [$FAKE_LOCALE]")

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser


def pynonymize(input_path, strategyfile_path, output_path, db_user, db_password, db_type=None, db_host=None, db_name=None, fake_locale=None):
    if db_type is None:
        db_type = "mysql"

    if db_host is None:
        db_host = "127.0.0.1"

    if db_name is None:
        db_name = get_temp_db_name(strategyfile_path)

    if fake_locale is None:
        fake_locale = "en_GB"

    validations = []
    if input_path is None:
        validations.append("Missing INPUT")

    if strategyfile_path is None:
        validations.append("Missing STRATEGYFILE")

    if output_path is None:
        validations.append("Missing OUTPUT")

    if db_user is None:
        validations.append("Missing DB_USER")

    if db_password is None:
        validations.append("Missing DB_PASSWORD")

    if len(validations) > 0:
        raise ArgumentValidationError(validations)

    fake_seeder = FakeColumnSet(fake_locale)
    strategy_parser = StrategyParser(fake_seeder)

    logger.debug("loading strategyfile %s...", strategyfile_path)
    with open(strategyfile_path, "r") as strategy_yaml:
        strategy = strategy_parser.parse_config(yaml.safe_load(strategy_yaml))

    # init and validate DB connection
    logger.debug("Database: (%s)%s@%s db_name: %s", db_host, db_type, db_user, db_name)
    db_provider = get_provider(db_type, db_host, db_user, db_password, db_name)

    if not db_provider.test_connection():
        raise DatabaseConnectionError()

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


def main(rawArgs=None):
    """
    Main entry point for the command line. Parse the cmdargs, load env and call to the main process
    :param args:
    :return:
    """
    # find the dotenv from the current working dir rather than the execution location
    dotenv_file = dotenv.find_dotenv(usecwd=True)
    dotenv.load_dotenv(dotenv_path=dotenv_file)

    parser = create_parser()
    args = parser.parse_args(rawArgs)

    # legacy posistionals take precendence if specified
    # This is to support those not using the new options/env fallbacks
    input        = args.legacy_input or args.input
    strategyfile = args.legacy_strategyfile or args.strategyfile
    output = args.legacy_output or args.output

    try:
        pynonymize(
            input_path=input,
            strategyfile_path=strategyfile,
            output_path=output,
            db_type=args.db_type,
            db_host=args.db_host,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            fake_locale=args.fake_locale
        )
    except DatabaseConnectionError as error:
        logger.error("Failed to connect to database.")
        sys.exit(1)
    except ArgumentValidationError as error:
        logger.error("Missing values for required arguments: \n" + "\n".join(error.validation_messages) +
                     "\nSet these using the command-line options or with environment variables. \n"
                     "For a complete list, See the program help below.\n")
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
