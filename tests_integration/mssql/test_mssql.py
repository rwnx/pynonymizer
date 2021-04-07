import pytest
import subprocess
import os
import tempfile
import shutil
import pyodbc


user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
test_dir = os.path.dirname(os.path.realpath(__file__))

abs_input = os.path.abspath(os.path.join(test_dir, "./sakila.bak"))
tmpdir = tempfile.gettempdir()
tmp_input = os.path.join(tmpdir, "sakila.bak")
tmp_output = os.path.join(tmpdir, "basic.bak")

# should make input available at /tmp/pagila.bak 0777
shutil.copyfile(abs_input, tmp_input)
os.chmod(tmp_input, 0o777)


def test_basic():
    """
        Perform an actual run against the local database using the modified sakila DB
        perform some basic checks against the output file
    """
    output = subprocess.check_output([
        "pynonymizer",
        "-i", tmp_input,
        "-o", tmp_output,
        "-s", "sakila.yml",
        "-t", "mssql"
        ],
        cwd=test_dir
    )

    # some very rough output checks
    assert os.path.exists(tmp_output)

def test_anonymize():
    output = subprocess.check_output([
        "pynonymizer",
        "-i", tmp_input,
        "-o", tmp_output,
        "-s", "sakila.yml",
        "-t", "mssql",
        "--db-name", "test_mssql",
        "--stop-at", "ANONYMIZE_DB"
        ],
        cwd=test_dir
    )
    driver = [i for i in pyodbc.drivers() if "sql server" in i.lower()][0]
    conn = pyodbc.connect(
        driver=driver,
        uid=user, 
        pwd=password,
        database="test_mssql",
        server="(local)",
        autocommit=True
    )
    agg_names = conn.execute("SELECT COUNT(1), first_name FROM actor GROUP BY first_name;").fetchall()

    print(agg_names)

    # make sure that names was actually randomized instead of simply set to the same value "randomly" 
    assert len(agg_names) > 1


    