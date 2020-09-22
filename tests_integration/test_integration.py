import pytest
import subprocess
import os

user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
test_dir = os.path.dirname(os.path.realpath(__file__))
ONE_MB = 1024 * 1024

@pytest.mark.integration
def test_basic():
    """
        Perform an actual run against the local database using the modified sakila DB
        perform some basic checks against the output file
    """
    output = subprocess.check_output([
        "pynonymizer",
        "-i", os.path.join(test_dir, "sakila.sql.gz"),
        "-o", os.path.join(test_dir, "output.sql"),
        "-s", os.path.join(test_dir, "sakila.yml")
        ]
    )
    output_path = os.path.join(test_dir, "./output.sql")

    # some very rough output checks
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 3 * ONE_MB

