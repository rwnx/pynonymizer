import pytest
import os
import pyodbc


from typer.testing import CliRunner

from pynonymizer.cli import app

user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
test_dir = os.path.dirname(os.path.realpath(__file__))
input_path = os.path.abspath(os.path.join(test_dir, "./sakila.bak"))
strategy_path = os.path.abspath(os.path.join(test_dir, "./sakila.yml"))

runner = CliRunner()


# https://learn.microsoft.com/en-us/dotnet/api/system.data.sqlclient.sqlconnection.connectionstring


def test_smoke_use_connection_str():
    """
    Perform an actual run against the local database using the modified sakila DB
    perform some basic checks against the output file
    """
    with runner.isolated_filesystem() as tmpdir:
        os.chmod(tmpdir, mode=0o777)
        tmp_output = os.path.join(tmpdir, "basic.bak")

        result = runner.invoke(
            app,
            [
                "-i",
                input_path,
                "-o",
                tmp_output,
                "-s",
                strategy_path,
                "-t",
                "mssql",
                "--mssql-connection-string",
                "Max Pool Size=50",
            ],
            catch_exceptions=False,
        )

        print(result.stdout)
        assert result.exit_code == 0
        # some very rough output checks
        assert os.path.exists(tmp_output)



def test_anonymize_column_uniqueness():
    with runner.isolated_filesystem() as tmpdir:
        tmp_output = os.path.join(tmpdir, "basic.bak")

        output = runner.invoke(
            app,
            [
                "-i",
                input_path,
                "-o",
                tmp_output,
                "-s",
                strategy_path,
                "-t",
                "mssql",
                "--db-name",
                "test_mssql",
                "--stop-at",
                "ANONYMIZE_DB",
            ],
            catch_exceptions=False,
        )
        print(result.stdout)

    assert output.exit_code == 0

    driver = [i for i in pyodbc.drivers() if "sql server" in i.lower()][0]
    conn = pyodbc.connect(
        driver=driver,
        uid=user,
        pwd=password,
        database="test_mssql",
        server="(local)",
        autocommit=True,
    )
    agg_names = conn.execute(
        "SELECT COUNT(1), first_name FROM actor GROUP BY first_name;"
    ).fetchall()

    print(agg_names)

    # make sure that names was actually randomized instead of simply set to the same value "randomly"
    assert len(agg_names) > 1
