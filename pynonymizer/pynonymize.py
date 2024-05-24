from dataclasses import dataclass
import logging
from typing import Optional
from pynonymizer.database.mssql import MsSqlProvider
from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.database.postgres import PostgreSqlProvider
from pynonymizer.strategy.parser import StrategyParser
from pynonymizer.strategy.config import read_config
from pynonymizer.exceptions import ArgumentValidationError
from pynonymizer.process_steps import ProcessSteps
from pynonymizer.strategy.database import DatabaseStrategy

import uuid
import os

logger = logging.getLogger(__name__)


def get_temp_db_name(filename=None):
    name, _ = os.path.splitext(os.path.basename(filename))
    return f"{name}_{uuid.uuid4().hex}"


def pynonymize(
    progress,
    actions,
    db_type,
    db_workers,
    input_path=None,
    strategyfile_path=None,
    output_path=None,
    db_user=None,
    db_password=None,
    db_host=None,
    db_name=None,
    db_port=None,
    seed_rows=None,
    ignore_anonymization_errors=False,
    **kwargs,
):
    """
    Runs a pynonymize process as if the CLI had been invoked.

    :raises:
        ArgumentValidationError: used when kwargs are missing or unable to be auto-resolved.

    """
    # Validate mandatory args (depends on step actions)
    validations = []

    if not actions.skipped(ProcessSteps.RESTORE_DB):
        if input_path is None:
            validations.append("Missing INPUT")

    if not actions.skipped(ProcessSteps.ANONYMIZE_DB):
        if strategyfile_path is None:
            validations.append("Missing STRATEGYFILE")
        else:
            # only auto-determine the db_name if we have a strategyfile AND we are anonymizing.
            if db_name is None:
                db_name = get_temp_db_name(strategyfile_path)

    if not actions.skipped(ProcessSteps.DUMP_DB):
        if output_path is None:
            validations.append("Missing OUTPUT")

    # do not validate db_user/password as these are managed by providers
    # Mysql supports my.cnf files with additional config, so we have to assume db_host, db_user, db_password, db_port could all be in there
    # postgres supports implicit db_pass using the .pgpass file
    # mssql could be using integrated security or connectionstr

    if db_name is None:
        validations.append("Missing DB_NAME: Auto-resolve failed.")

    # Discover db-type kwargs
    # mssql_backup_option -> backup_option and pass these to the constructor
    db_kwargs = {}
    db_arg_prefix = f"{db_type}_"
    for k, v in kwargs.items():
        if k.startswith(db_arg_prefix):
            db_kwargs[k[len(db_arg_prefix) :]] = v

    logger.debug(
        "Database: (%s:%s)%s@%s name: %s", db_host, db_port, db_type, db_user, db_name
    )

    if db_type == "mysql":
        Provider = MySqlProvider
    elif db_type == "postgres":
        Provider = PostgreSqlProvider
    elif db_type == "mssql":
        Provider = MsSqlProvider
    else:
        validations.append(f"{db_type} is not a known database type.")

    if len(validations) > 0:
        raise ArgumentValidationError(validations)

    # init strategy as it relies on I/O - fail fast here preferred to after restore
    if not actions.skipped(ProcessSteps.ANONYMIZE_DB):
        strategy_parser = StrategyParser()

        logger.debug("loading strategyfile %s...", strategyfile_path)
        file_data = read_config(strategyfile_path)
        strategy = strategy_parser.parse_config(file_data)

    db_provider = Provider(
        db_host=db_host,
        db_user=db_user,
        db_pass=db_password,
        db_name=db_name,
        db_port=db_port,
        seed_rows=seed_rows,
        progress=progress,
        **db_kwargs,
    )

    # main process - no destructive/non-retryable actions should happen before this line ---
    logger.info(actions.summary(ProcessSteps.CREATE_DB))
    if not actions.skipped(ProcessSteps.CREATE_DB):
        db_provider.create_database()

    logger.info(actions.summary(ProcessSteps.RESTORE_DB))
    if not actions.skipped(ProcessSteps.RESTORE_DB):
        db_provider.restore_database(input_path)

    logger.info(actions.summary(ProcessSteps.ANONYMIZE_DB))
    if not actions.skipped(ProcessSteps.ANONYMIZE_DB):
        try:
            db_provider.anonymize_database(strategy, db_workers=db_workers)
        except Exception as e:
            if not ignore_anonymization_errors:
                raise e

    logger.info(actions.summary(ProcessSteps.DUMP_DB))
    if not actions.skipped(ProcessSteps.DUMP_DB):
        db_provider.dump_database(output_path)

    logger.info(actions.summary(ProcessSteps.DROP_DB))
    if not actions.skipped(ProcessSteps.DROP_DB):
        db_provider.drop_database()

    logger.info("Process complete!")
