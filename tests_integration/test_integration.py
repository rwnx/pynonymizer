import pytest
import subprocess
import os

user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
test_dir = os.path.dirname(os.path.realpath(__file__))
ONE_MB = 1024 * 1024

@pytest.mark.integration
def test_smoke_lzma():
    output = subprocess.check_output([
        "pynonymizer",
        "-i", "sakila.sql.gz",
        "-o", "basic.sql.xz",
        "-s", "sakila.yml"
        ],
        cwd=test_dir
    )
    output_path = os.path.join(test_dir, "./basic.sql.xz")

    # some very rough output checks
    assert os.path.exists(output_path)

@pytest.mark.integration
def test_basic():
    """
        Perform an actual run against the local database using the modified sakila DB
        perform some basic checks against the output file
    """
    output = subprocess.check_output([
        "pynonymizer",
        "-i", "sakila.sql.gz",
        "-o", "basic.sql",
        "-s", "sakila.yml"
        ],
        cwd=test_dir
    )
    output_path = os.path.join(test_dir, "./basic.sql")

    # some very rough output checks
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 3 * ONE_MB

@pytest.mark.integration
def test_basic_stdin_stdout():
    p = subprocess.check_output(f"gunzip -c sakila.sql.gz | pynonymizer -i - -o - -s sakila.yml > stdout.sql", shell=True, cwd=test_dir )

    output_path = os.path.join(test_dir, "./stdout.sql")
    # some very rough output checks
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 3 * ONE_MB

