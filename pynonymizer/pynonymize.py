from enum import Enum
import yaml
from pynonymizer import input, output
from pynonymizer.log import get_default_logger
from pynonymizer.database import get_temp_db_name, get_provider
from pynonymizer.fake import FakeColumnSet
from pynonymizer.strategy.parser import StrategyParser
from pynonymizer.exceptions import ArgumentValidationError, DatabaseConnectionError


logger = get_default_logger()


class ProcessSteps(Enum):
    START = 0
    GET_SOURCE = 100
    CREATE_DB = 200
    RESTORE_DB = 300
    ANONYMIZE_DB = 400
    DUMP_DB = 500
    DROP_DB = 600
    END = 9999

    @staticmethod
    def names():
        return [step.name for step in ProcessSteps]

    @staticmethod
    def from_value(step_value):
        """
        resolve a enum value from key or value
        :return: ProcessSteps property
        """
        try:
            # Try to resolve as a string value
            return ProcessSteps[step_value]
        except KeyError:
            # If that fails, it must be a value
            # If this fails, the resulting ValueError will bubble out -invalid data!
            return ProcessSteps(step_value)


def _run_step(process_step, start_at_step, stop_at_step, skip_steps, func):
    if start_at_step.value > process_step.value:
        logger.warning(f"Skipping [{process_step.name}] (Starting at [{start_at_step.name}])")
        return False
    elif stop_at_step.value < process_step.value:
        logger.warning(f"Skipping [{process_step.name}] (Stopped at [{stop_at_step.name}])")
        return False
    elif skip_steps and process_step in skip_steps:
        logger.warning(f"Skipping [{process_step.name}] (skip-steps)")
        return False
    else:
        logger.info(f"Running [{process_step.name}]")
        func()
        return True


def pynonymize(input_path=None, strategyfile_path=None, output_path=None, db_user=None, db_password=None, db_type=None,
               db_host=None, db_name=None, fake_locale=None, start_at_step=None, stop_at_step=None, skip_steps=None):

    # Validate mandatory args
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

    # Default and Normalize args
    if db_type is None:
        db_type = "mysql"

    if db_host is None:
        db_host = "127.0.0.1"

    if db_name is None:
        db_name = get_temp_db_name(strategyfile_path)

    if fake_locale is None:
        fake_locale = "en_GB"

    if start_at_step is None:
        start_at_step = ProcessSteps.START
    else:
        start_at_step = ProcessSteps.from_value(start_at_step)

    if stop_at_step is None:
        stop_at_step = ProcessSteps.END
    else:
        stop_at_step = ProcessSteps.from_value(stop_at_step)

    if skip_steps and len(skip_steps) > 0:
        skip_steps = [ProcessSteps.from_value(skip) for skip in skip_steps]

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
    _run_step(ProcessSteps.CREATE_DB, start_at_step, stop_at_step, skip_steps,
              lambda: db_provider.create_database())

    _run_step(ProcessSteps.RESTORE_DB, start_at_step, stop_at_step, skip_steps,
              lambda: db_provider.restore_database(input_obj))

    _run_step(ProcessSteps.ANONYMIZE_DB, start_at_step, stop_at_step, skip_steps,
              lambda: db_provider.anonymize_database(strategy))

    _run_step(ProcessSteps.DUMP_DB, start_at_step, stop_at_step, skip_steps,
              lambda: db_provider.dump_database(output_obj))

    _run_step(ProcessSteps.DROP_DB, start_at_step, stop_at_step, skip_steps,
              lambda: db_provider.drop_database())

    logger.info("Process complete!")