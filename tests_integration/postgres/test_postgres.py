import pytest
import subprocess
import os

# force getenv to error here for more human-readable errors
user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
test_dir = os.path.dirname(os.path.realpath(__file__))
ONE_MB = 1024 * 1024


def test_basic():
    """
        Perform an actual run against the local database using the modified sakila DB
        perform some basic checks against the output file
    """
    output = subprocess.check_output([
        "pynonymizer",
        "-i", "pagila.sql",
        "-o", "basic.sql",
        "-s", "pagila.yml",
        "-t", "postgres"
        ],
        cwd=test_dir
    )
    output_path = os.path.join(test_dir, "./basic.sql")

    # some very rough output checks
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 3 * ONE_MB
