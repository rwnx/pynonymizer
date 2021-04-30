import pytest
import subprocess
import os

# force getenv to error here for more human-readable errors
user = os.getenv("PYNONYMIZER_DB_USER")
password = os.getenv("PYNONYMIZER_DB_PASSWORD")
host = os.getenv("PYNONYMIZER_DB_HOST")

test_dir = os.path.dirname(os.path.realpath(__file__))

def get_single(db, query):
    return subprocess.check_output(f"psql -qtAX --user {user} -d {db} -h {host} -c '{query}'", shell=True, env={"PGPASSWORD": password}).decode().split("\n")[0]


def test_basic():
    """
        Perform an actual run against the local database using the modified sakila DB
        perform some basic checks against the output file
    """
    output = subprocess.check_output([
        "pynonymizer",
        "-i", "pagila.sql.gz",
        "-o", "basic.sql",
        "-s", "pagila.yml",
        "-t", "postgres"
        ],
        cwd=test_dir
    )
    output_path = os.path.join(test_dir, "./basic.sql")

    # some very rough output checks
    assert os.path.exists(output_path)

def test_anonymize_column_uniqueness():
    output = subprocess.check_output([
        "pynonymizer",
        "-i", "pagila.sql.gz",
        "-o", "basic.sql",
        "-s", "sakila.yml",
        "-t", "postgres",
        "--db-name", "test_postgres",
        "--stop-at", "ANONYMIZE_DB"
        ],
        cwd=test_dir
    )
    query = "WITH names_agg AS (SELECT COUNT(1), first_name FROM actor GROUP BY first_name) SELECT COUNT(1) FROM names_agg"
    name_count = int(get_single("test_postgres", query))

    print(name_count)

    # make sure that names was actually randomized instead of simply set to the same value "randomly" 
    assert name_count > 1