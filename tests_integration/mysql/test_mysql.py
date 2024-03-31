import gzip
import shutil
import pytest
import subprocess
import os
import unittest
from pynonymizer.cli import app
from typer.testing import CliRunner

# force getenv to error here for more human-readable errors
user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
test_dir = os.path.dirname(os.path.realpath(__file__))
input_path = os.path.abspath(os.path.join(test_dir, "./sakila.sql.gz"))
strategy_path = os.path.abspath(os.path.join(test_dir, "./sakila.yml"))
ONE_MB = 1024 * 1024

home = os.path.expanduser("~")
config_path = os.path.join(home, ".my.cnf")

os.chdir(test_dir)

runner = CliRunner()


class OptionalConfigTests(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        with open(config_path, "w+") as f:
            f.write(
                f"""
[client]
user="{user}"
password="{password}"
                """
            )

    def test_smoke_lzma(self):
        new_env = os.environ.copy()
        del new_env["PYNONYMIZER_DB_USER"]
        del new_env["PYNONYMIZER_DB_PASSWORD"]

        with runner.isolated_filesystem() as tmpdir:
            output_path = os.path.join(tmpdir, "basic.sql.xz")
            output = runner.invoke(
                app,
                ["-i", input_path, "-o", output_path, "-s", strategy_path],
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


def test_smoke_lzma():
    with runner.isolated_filesystem() as tmpdir:
        output_path = os.path.join(tmpdir, "basic.sql.xz")
        output = runner.invoke(
            app,
            ["-i", input_path, "-o", output_path, "-s", strategy_path],
            catch_exceptions=False,
        )
        print(output.stdout)

        assert output.exit_code == 0

        # some very rough output checks
        assert os.path.exists(output_path)


def test_basic():
    with runner.isolated_filesystem() as tmpdir:
        output_path = os.path.join(tmpdir, "basic.sql")
        output = runner.invoke(
            app,
            ["-i", input_path, "-o", output_path, "-s", strategy_path],
            catch_exceptions=False,
        )
        print(output.stdout)
        assert output.exit_code == 0

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 3 * ONE_MB


def test_parallel():
    with runner.isolated_filesystem() as tmpdir:
        output_path = os.path.join(tmpdir, "basic.sql")
        output = runner.invoke(
            app,
            [
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

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 3 * ONE_MB


def test_basic_stdin_stdout():
    with gzip.open(input_path) as gzip_file:
        gzip_raw = gzip_file.read()

        output = runner.invoke(
            app,
            ["-i", "-", "-o", "-", "-s", strategy_path],
            input=gzip_raw,
            catch_exceptions=False,
        )

        # dont print stdout unless you wanna see the whole dump
        # print(output.stdout)
        assert output.exit_code == 0
        assert len(output.stdout) > 3 * ONE_MB
