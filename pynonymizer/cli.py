from subprocess import CalledProcessError
from typing import Annotated, List
import sys
import logging
import typer
from pynonymizer.exceptions import DatabaseConnectionError
from pynonymizer.fake import UnsupportedFakeArgumentsError, UnsupportedFakeTypeError
from pynonymizer.process_steps import StepActionMap
from pynonymizer.pynonymize import (
    ArgumentValidationError,
    pynonymize,
    ProcessSteps,
)
from pynonymizer import __version__
from tqdm import tqdm

app = typer.Typer()


def version_callback(value: bool):
    if value:
        print(f"{__version__}")
        raise typer.Exit()


@app.command(context_settings={"auto_envvar_prefix": "PYNONYMIZER"})
def default(
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
    db_workers: Annotated[int, typer.Option("--workers", "-w")] = 1,
    start_at_step: Annotated[
        str,
        typer.Option(
            "--start-at", help="Choose a step to begin the process (inclusive)."
        ),
    ] = "START",
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
    ] = "END",
    seed_rows: Annotated[
        int,
        typer.Option(
            min=1,
            show_envvar=True,
            help="Number of rows to populate the fake data table used during anonymization",
        ),
    ] = 150,
    mssql_connection_string: Annotated[
        str,
        typer.Option(
            "--mssql-connection-string",
            "-c",
            help="Pass additional options to the pyodbc connection. overrides existing connection arguments.",
        ),
    ] = None,
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
    mssql_ansi_warnings_off: Annotated[
        bool,
        typer.Option(
            "--mssql-ansi-warnings-off",
            help="[mssql] turn off ANSI_WARNINGS when making updates.",
        ),
    ] = True,
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

    root_logger = logging.getLogger()

    loglevel = logging.INFO
    if verbose:
        loglevel = logging.DEBUG

    root_logger.handlers.clear()
    console_handler = logging.StreamHandler(sys.stderr)

    console_handler.setLevel(loglevel)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(console_handler)

    # Default and Normalize args
    if only_step is not None:
        only_step = ProcessSteps.from_value(only_step)

    start_at_step = ProcessSteps.from_value(start_at_step)
    stop_at_step = ProcessSteps.from_value(stop_at_step)

    if skip_steps and len(skip_steps) > 0:
        skip_steps = [ProcessSteps.from_value(skip) for skip in skip_steps]

    if verbose:
        console_handler.setLevel(logging.DEBUG)

    actions = StepActionMap(
        start_at_step=start_at_step,
        stop_at_step=stop_at_step,
        skip_steps=skip_steps,
        dry_run=dry_run,
        only_step=only_step,
    )

    # Add local project dir to path in case of custom provider imports
    if "." not in sys.path:
        sys.path.append(".")
    try:
        pynonymize(
            progress=tqdm,
            actions=actions,
            input_path=input,
            strategyfile_path=strategyfile,
            output_path=output,
            seed_rows=seed_rows,
            mssql_driver=mssql_driver,
            mssql_backup_compression=mssql_backup_compression,
            mysql_cmd_opts=mysql_cmd_opts,
            mysql_dump_opts=mysql_dump_opts,
            postgres_cmd_opts=postgres_cmd_opts,
            postgres_dump_opts=postgres_dump_opts,
            ignore_anonymization_errors=ignore_anonymization_errors,
            verbose=verbose,
            db_type=db_type,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            db_workers=db_workers,
            mssql_connection_string=mssql_connection_string,
            mssql_ansi_warnings_off=mssql_ansi_warnings_off,
        )
    except ModuleNotFoundError as error:
        if error.name == "pyodbc" and db_type == "mssql":
            root_logger.error("Missing Required Packages for database support.")
            root_logger.error("Install package extras: pip install pynonymizer[mssql]")
            return typer.Exit(1)
        else:
            raise error
    except ImportError as error:
        if error.name == "pyodbc" and db_type == "mssql":
            root_logger.error(
                "Error importing pyodbc (mssql). "
                "The ODBC driver may not be installed on your system. See package `unixodbc`."
            )
            return typer.Exit(1)
        else:
            raise error
    except DatabaseConnectionError as error:
        root_logger.error("Failed to connect to database.")
        if verbose:
            root_logger.error(error)
        return typer.Exit(1)
    except ArgumentValidationError as error:
        root_logger.error(
            "Missing values for required arguments: \n"
            + "\n".join(error.validation_messages)
            + "\nSet these using the command-line options or with environment variables. \n"
            "For a complete list, See: `pynonymizer --help`.\n"
        )
        return typer.Exit(2)
    except UnsupportedFakeArgumentsError as error:
        root_logger.error(
            f"There was an error while parsing the strategyfile. Unknown fake type: {error.fake_type} \n "
            + f"This happens when additional kwargs are passed to a fake type that it doesnt support. \n"
            + f"You can only configure generators using kwargs that Faker supports. \n"
            + f"See https://github.com/rwnx/pynonymizer/blob/main/doc/strategyfiles.md#column-strategy-fake_update for usage information."
        )
        return typer.Exit(1)
    except UnsupportedFakeTypeError as error:
        root_logger.error(
            f"There was an error while parsing the strategyfile. Unknown fake type: {error.fake_type} \n "
            + f"This happens when an fake_update column strategy is used with a generator that doesn't exist. \n"
            + f"You can only use data types that Faker supports. \n"
            + f"See https://github.com/rwnx/pynonymizer/blob/main/doc/strategyfiles.md#column-strategy-fake_update for usage information."
        )
        return typer.Exit(1)
    except CalledProcessError as error:
        root_logger.error(error)
        return typer.Exit(1)


def cli():
    app()


if __name__ == "__main__":
    cli()
