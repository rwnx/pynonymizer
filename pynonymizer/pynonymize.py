import yaml
from pynonymizer import input, output
from pynonymizer.log import get_default_logger
from pynonymizer.database import get_temp_db_name, get_provider
from pynonymizer.fake import FakeColumnGenerator
from pynonymizer.strategy.parser import StrategyParser
from pynonymizer.exceptions import ArgumentValidationError, DatabaseConnectionError
from pynonymizer.process_steps import StepActionMap, ProcessSteps


logger = get_default_logger()


def pynonymize(input_path=None, strategyfile_path=None, output_path=None, db_user=None, db_password=None, db_type=None,
               db_host=None, db_name=None, fake_locale=None, start_at_step=None, stop_at_step=None, skip_steps=None):

    # Default and Normalize args
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

    if db_type is None:
        db_type = "mysql"

    if db_host is None:
        db_host = "127.0.0.1"

    if db_name is None:
        db_name = get_temp_db_name(strategyfile_path)

    if fake_locale is None:
        fake_locale = "en_GB"

    actions = StepActionMap(start_at_step, stop_at_step, skip_steps)

    # Validate mandatory args (depends on step actions)
    validations = []

    if not actions.skipped(ProcessSteps.RESTORE_DB):
        if input_path is None:
            validations.append("Missing INPUT")

    if not actions.skipped(ProcessSteps.ANONYMIZE_DB):
        if strategyfile_path is None:
            validations.append("Missing STRATEGYFILE")

    if not actions.skipped(ProcessSteps.DUMP_DB):
        if output_path is None:
            validations.append("Missing OUTPUT")

    if db_user is None:
        validations.append("Missing DB_USER")

    if db_password is None:
        validations.append("Missing DB_PASSWORD")

    if len(validations) > 0:
        raise ArgumentValidationError(validations)


    fake_seeder = FakeColumnGenerator(fake_locale)
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
    logger.info(actions.summary(ProcessSteps.CREATE_DB))
    if not actions.skipped(ProcessSteps.CREATE_DB):
        db_provider.create_database()

    logger.info(actions.summary(ProcessSteps.RESTORE_DB))
    if not actions.skipped(ProcessSteps.RESTORE_DB):
        db_provider.restore_database(input_obj)

    logger.info(actions.summary(ProcessSteps.ANONYMIZE_DB))
    if not actions.skipped(ProcessSteps.ANONYMIZE_DB):
        db_provider.anonymize_database(strategy)

    logger.info(actions.summary(ProcessSteps.DUMP_DB))
    if not actions.skipped(ProcessSteps.DUMP_DB):
        db_provider.dump_database(output_obj)

    logger.info(actions.summary(ProcessSteps.DROP_DB))
    if not actions.skipped(ProcessSteps.DROP_DB):
        db_provider.drop_database()

    logger.info("Process complete!")