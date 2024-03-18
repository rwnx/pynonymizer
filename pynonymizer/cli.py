import argparse
from typing import Annotated, List, Optional, Union
import dotenv
import os
import sys
import logging
import typer
from pynonymizer.fake import UnsupportedFakeArgumentsError, UnsupportedFakeTypeError
from pynonymizer.pynonymize import (
    ArgumentValidationError,
    DatabaseConnectionError,
    pynonymize,
    ProcessSteps,
)
from pynonymizer import __version__


app = typer.Typer()


def version_callback(value: bool):
    if value:
        print(f"{__version__}")
        raise typer.Exit()


@app.command(context_settings={"auto_envvar_prefix": "PYNONYMIZER"})
def main(
    input: Annotated[
        str,
        typer.Option(
            "--input",
            "-i",
            help="The source dump filepath to read from. Use `-` for stdin.",
        ),
    ] = None,
    strategyfile: Annotated[
        str,
        typer.Option(
            "--strategy", "-s", help="A strategyfile to use during anonymization."
        ),
    ] = None,
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="The destination filepath to write the dumped output to. Use `-` for stdout.",
        ),
    ] = None,
    db_type: Annotated[str, typer.Option("--db-type", "-t")] = "mysql",
    db_host: Annotated[str, typer.Option("--db-host", "-d")] = None,
    db_port: Annotated[str, typer.Option("--db-port", "-P")] = None,
    db_name: Annotated[str, typer.Option("--db-name", "-n")] = None,
    db_user: Annotated[str, typer.Option("--db-user", "-u")] = None,
    db_password: Annotated[str, typer.Option("--db-password", "-p")] = None,
    start_at_step: Annotated[
        str,
        typer.Option(
            "--start-at", help="Choose a step to begin the process (inclusive)."
        ),
    ] = None,
    only_step: Annotated[str, typer.Option(help="Choose one step to perform.")] = None,
    skip_steps: Annotated[
        List[str],
        typer.Option(
            "--skip_steps",
            show_envvar=True,
            help="Choose one or more steps to skip",
            case_sensitive=False,
        ),
    ] = None,
    stop_at_step: Annotated[
        str,
        typer.Option("--stop-at", help="Choose a step to stop at (inclusive)."),
    ] = None,
    seed_rows: Annotated[
        int,
        typer.Option(
            min=1,
            show_envvar=True,
            help="Number of rows to populate the fake data table used during anonymization",
        ),
    ] = 150,
    mssql_driver: Annotated[
        str,
        typer.Option(
            "--mssql-backup-compression",
            help="[mssql] ODBC driver to use for database connection.",
        ),
    ] = None,
    mssql_backup_compression: Annotated[
        bool,
        typer.Option(
            "--mssql-backup-compression",
            help="[mssql] Use compression when backing up the database.",
        ),
    ] = False,
    mysql_cmd_opts: Annotated[
        str,
        typer.Option(
            "--mysql-cmd-opts",
            help="[mysql] pass additional arguments to the restore process.",
        ),
    ] = None,
    mysql_dump_opts: Annotated[
        str,
        typer.Option(
            "--mysql-cmd-opts",
            help="[mysql] pass additional arguments to the dump process.",
        ),
    ] = None,
    postgres_cmd_opts: Annotated[
        str,
        typer.Option(
            "--mysql-cmd-opts",
            help="[postgres] pass additional arguments to the restore process.",
        ),
    ] = None,
    postgres_dump_opts: Annotated[
        str,
        typer.Option(
            "--mysql-cmd-opts",
            help="[postgres] pass additional arguments to the dump process.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Skip all process steps. Useful for testing safely."
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Increases the verbosity of the logging feature, to help when troubleshooting issues.",
        ),
    ] = False,
    ignore_anonymization_errors: Annotated[
        bool,
        typer.Option(
            "--ignore-anonymization-errors",
            help="Ignore errors during the anonymization process.",
        ),
    ] = False,
    version: Annotated[
        bool, typer.Option("--version", callback=version_callback, is_eager=True)
    ] = False,
):
    """
    A tool for writing better anonymization strategies for your production databases.

    https://github.com/rwnx/pynonymizer
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logger.handlers.clear()
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    # find the dotenv from the current working dir rather than the execution location
    dotenv_file = dotenv.find_dotenv(usecwd=True)
    dotenv.load_dotenv(dotenv_path=dotenv_file)

    if verbose:
        console_handler.setLevel(logging.DEBUG)

    # Add local project dir to path in case of custom provider imports
    if "." not in sys.path:
        sys.path.append(".")
    try:
        pynonymize(
            input_path=input,
            strategyfile_path=strategyfile,
            output_path=output,
            db_type=db_type,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            start_at_step=start_at_step,
            only_step=only_step,
            skip_steps=skip_steps,
            stop_at_step=stop_at_step,
            seed_rows=seed_rows,
            mssql_driver=mssql_driver,
            mssql_backup_compression=mssql_backup_compression,
            mysql_cmd_opts=mysql_cmd_opts,
            mysql_dump_opts=mysql_dump_opts,
            postgres_cmd_opts=postgres_cmd_opts,
            postgres_dump_opts=postgres_dump_opts,
            dry_run=dry_run,
            verbose=verbose,
            ignore_anonymization_errors=ignore_anonymization_errors,
        )
    except ModuleNotFoundError as error:
        if error.name == "pyodbc" and db_type == "mssql":
            logger.error("Missing Required Packages for database support.")
            logger.error("Install package extras: pip install pynonymizer[mssql]")
            sys.exit(1)
        else:
            raise error
    except ImportError as error:
        if error.name == "pyodbc" and db_type == "mssql":
            logger.error(
                "Error importing pyodbc (mssql). "
                "The ODBC driver may not be installed on your system. See package `unixodbc`."
            )
            sys.exit(1)
        else:
            raise error
    except DatabaseConnectionError as error:
        logger.error("Failed to connect to database.")
        if verbose:
            logger.error(error)
        sys.exit(1)
    except ArgumentValidationError as error:
        logger.error(
            "Missing values for required arguments: \n"
            + "\n".join(error.validation_messages)
            + "\nSet these using the command-line options or with environment variables. \n"
            "For a complete list, See the program help below.\n"
        )
        sys.exit(2)
    except UnsupportedFakeArgumentsError as error:
        logger.error(
            f"There was an error while parsing the strategyfile. Unknown fake type: {error.fake_type} \n "
            + f"This happens when additional kwargs are passed to a fake type that it doesnt support. \n"
            + f"You can only configure generators using kwargs that Faker supports. \n"
            + f"See https://github.com/rwnx/pynonymizer/blob/main/doc/strategyfiles.md#column-strategy-fake_update for usage information."
        )
        sys.exit(1)
    except UnsupportedFakeTypeError as error:
        logger.error(
            f"There was an error while parsing the strategyfile. Unknown fake type: {error.fake_type} \n "
            + f"This happens when an fake_update column strategy is used with a generator that doesn't exist. \n"
            + f"You can only use data types that Faker supports. \n"
            + f"See https://github.com/rwnx/pynonymizer/blob/main/doc/strategyfiles.md#column-strategy-fake_update for usage information."
        )
        sys.exit(1)


def cli():
    app()


if __name__ == "__main__":
    cli()
