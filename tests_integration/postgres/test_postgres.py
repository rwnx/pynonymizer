import gzip
import pytest
import subprocess
import os
import unittest
from typer.testing import CliRunner
from pynonymizer.cli import app

# force getenv to error here for more human-readable errors
user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
host = os.getenv("PYNONYMIZER_DB_HOST")

test_dir = os.path.dirname(os.path.realpath(__file__))

home = os.path.expanduser("~")
config_path = os.path.join(home, ".pgpass")

input_path = os.path.abspath(os.path.join(test_dir, "./pagila.sql.gz"))
strategy_path = os.path.abspath(os.path.join(test_dir, "./pagila.yml"))
ONE_MB = 1024 * 1024

runner = CliRunner()


class OptionalConfigTests(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        with open(config_path, "w+") as f:
            f.write(
                f"""
*:*:*:*:{password}
"""
            )

        # postgres will not load a .pgpass file unless it has the correct permissions
        os.chmod(config_path, 0o600)

    def test_optional_config(self):
        new_env = os.environ.copy()
        del new_env["PYNONYMIZER_DB_PASSWORD"]
        # Rather than rely on the default loading behaviour of .pgpass, which seems to be iffy in CI
        # (and is definitely NOT the subject under test!) force it here with the PGPASSFILE env
        new_env["PGPASSFILE"] = config_path

        with runner.isolated_filesystem() as tmpdir:
            output_path = os.path.join(tmpdir, "output.sql.xz")
            output = runner.invoke(
                app,
                [
                    "--db-host",
                    host,
                    "--db-user",
                    user,
                    "--db-type",
                    "postgres",
                    "-i",
                    input_path,
                    "-o",
                    output_path,
                    "-s",
                    strategy_path,
                ],
                env=new_env,
                catch_exceptions=False,
            )
            print(output.stdout)
            assert output.exit_code == 0

            # some very rough output checks
            assert os.path.exists(output_path)

    @classmethod
    def teardown_class(cls):
        os.remove(config_path)


def get_single(db, query):
    return (
        subprocess.check_output(
            f"psql -qtAX --user {user} -d {db} -h {host} -c '{query}'",
            shell=True,
            env={"PGPASSWORD": password},
        )
        .decode()
        .split("\n")[0]
    )


def test_parallel():
    """
    Perform an actual run against the local database using the modified sakila DB
    perform some basic checks against the output file
    """
    with runner.isolated_filesystem() as tmpdir:
        output_path = os.path.join(tmpdir, "output.sql.xz")
        output = runner.invoke(
            app,
            [
                "--db-host",
                host,
                "--db-user",
                user,
                "--db-type",
                "postgres",
                "-i",
                input_path,
                "-o",
                output_path,
                "-s",
                strategy_path,
                "--workers",
                "3",
            ],
            catch_exceptions=False,
        )
        print(output.stdout)
        assert output.exit_code == 0

        # some very rough output checks
        assert os.path.exists(output_path)


def test_basic():
    """
    Perform an actual run against the local database using the modified sakila DB
    perform some basic checks against the output file
    """
    with runner.isolated_filesystem() as tmpdir:
        output_path = os.path.join(tmpdir, "output.sql.xz")
        output = runner.invoke(
            app,
            [
                "--db-host",
                host,
                "--db-user",
                user,
                "--db-type",
                "postgres",
                "-i",
                input_path,
                "-o",
                output_path,
                "-s",
                strategy_path,
            ],
            catch_exceptions=False,
        )
        print(output.stdout)
        assert output.exit_code == 0

        # some very rough output checks
        assert os.path.exists(output_path)


def test_anonymize_column_uniqueness():
    with runner.isolated_filesystem() as tmpdir:
        output_path = os.path.join(tmpdir, "output.sql")
        output = runner.invoke(
            app,
            [
                "--db-host",
                host,
                "--db-user",
                user,
                "--db-type",
                "postgres",
                "--db-name",
                "test_postgres",
                "--stop-at",
                "ANONYMIZE_DB",
                "-i",
                input_path,
                "-o",
                output_path,
                "-s",
                strategy_path,
            ],
            catch_exceptions=False,
        )
        print(output.stdout)
        assert output.exit_code == 0

    query = "WITH names_agg AS (SELECT COUNT(1), first_name FROM actor GROUP BY first_name) SELECT COUNT(1) FROM names_agg"
    name_count = int(get_single("test_postgres", query))

    print(name_count)

    # make sure that names was actually randomized instead of simply set to the same value "randomly"
    assert name_count > 1


def test_basic_stdin_stdout():
    with gzip.open(input_path) as gzip_file:
        gzip_raw = gzip_file.read()

        output = runner.invoke(
            app,
            [
                "--db-host",
                host,
                "--db-user",
                user,
                "--db-type",
                "postgres",
                "-i",
                "-",
                "-o",
                "-",
                "-s",
                strategy_path,
            ],
            input=gzip_raw,
            catch_exceptions=False,
        )

        # dont print stdout unless you wanna see the whole dump
        # print(output.stdout)
        assert output.exit_code == 0
        assert len(output.stdout) > 3 * ONE_MB
