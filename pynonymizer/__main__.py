import argparse
import dotenv
import os
import sys
from pynonymizer.pynonymize import ArgumentValidationError, DatabaseConnectionError, pynonymize, ProcessSteps
from pynonymizer.log import get_default_logger
from pynonymizer.version import __version__

logger = get_default_logger()


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
                        help="Type of database to interact with. More databases will be supported in future versions. default: mysql [$PYNONYMIZER_DB_TYPE]")

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
                        help="Locale setting to initialize fake data generation. Affects Names, addresses, formats, etc. [$PYNONYMIZER_FAKE_LOCALE]")

    parser.add_argument("--start-at",
                        default=os.getenv("PYNONYMIZER_START_AT"), dest="start_at_step", choices=ProcessSteps.names(), metavar="STEP",
                        help="Choose a step to begin the process (inclusive). [$PYNONYMIZER_START_AT]")

    parser.add_argument("--skip-steps",
                        nargs="+", required=False, choices=ProcessSteps.names(), metavar="STEP",
                        default=(lambda: os.getenv("PYNONYMIZER_SKIP_STEPS").split() if os.getenv("PYNONYMIZER_SKIP_STEPS") else [])(), dest="skip_steps",
                        help="Choose one or more steps to skip. [$PYNONYMIZER_SKIP_STEPS]")

    parser.add_argument("--stop-at",
                        default=os.getenv("PYNONYMIZER_STOP_AT"), dest="stop_at_step", choices=ProcessSteps.names(), metavar="STEP",
                        help="Choose a step to stop at (inclusive). [$PYNONYMIZER_STOP_AT]")

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser


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
            fake_locale=args.fake_locale,
            start_at_step=args.start_at_step,
            skip_steps=args.skip_steps,
            stop_at_step=args.stop_at_step
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
