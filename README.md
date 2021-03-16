# `pynonymizer` [![pynonymizer on PyPI](https://img.shields.io/pypi/v/pynonymizer)](https://pypi.org/project/pynonymizer/) [![Downloads](https://pepy.tech/badge/pynonymizer)](https://pepy.tech/project/pynonymizer) ![License](https://img.shields.io/pypi/l/pynonymizer)

pynonymizer is a universal tool for translating sensitive production database dumps into anonymized copies.

This can help you support GDPR/Data Protection in your organization without compromizing on quality testing data.

## Why are anonymized databases important?
The primary source of information on how your database is used is in _your production database_. In most situations, the production dataset is usually significantly larger than any development copy, and
would contain a wider range of data.

From time to time, it is prudent to run a new feature or stage a test against this dataset, rather
than one that is artificially created by developers or by testing frameworks. Anonymized databases allow us to use the structures present in production, while stripping them of any personally identifiable data that would
consitute a breach of privacy for end-users and subsequently a breach of GDPR.

With Anonymized databases, copies can be processed regularly, and distributed easily, leaving your developers and testers with a rich source of information on the volume and general makeup of the system in production. It can
be used to run better staging environments, integration tests, and even simulate database migrations.

below is an excerpt from an anonymized database:

| id |salutation | firstname | surname | email | dob |
| - | - | - | - | - | - |
| 1 | Dr. | Bernard | Gough | `tnelson@powell.com` | 2000-07-03 |
| 2 | Mr. | Molly | Bennett | `clarkeharriet@price-fry.com` | 2014-05-19 |
| 3 | Mrs. | Chelsea | Reid | `adamsamber@clayton.com` | 1974-09-08 |
| 4 | Dr. | Grace | Armstrong | `tracy36@wilson-matthews.com` | 1963-12-15 |
| 5 | Dr. | Stanley | James | `christine15@stewart.net` | 1976-09-16 |
| 6 | Dr. | Mark | Walsh | `dgardner@ward.biz` | 2004-08-28 |
| 7 | Mrs. | Josephine | Chambers | `hperry@allen.com` | 1916-04-04 |
| 8 | Dr. | Stephen | Thomas | `thompsonheather@smith-stevens.com` | 1995-04-17 |
| 9 | Ms. | Damian | Thompson | `yjones@cox.biz` | 2016-10-02 |
| 10 | Miss | Geraldine | Harris | `porteralice@francis-patel.com` | 1910-09-28 |
| 11 | Ms. | Gemma | Jones | `mandylewis@patel-thomas.net` | 1990-06-03 |
| 12 | Dr. | Glenn | Carr | `garnervalerie@farrell-parsons.biz` | 1998-04-19 |


## How does it work?
`pynonymizer` replaces personally identifiable data in your database with **realistic** pseudorandom data, from the `Faker` library or from other functions.
There are a wide variety of data types available which should suit the column in question, for example:

* `unique_email`
* `company`
* `file_path`
* `[...]`

For a full list of data generation strategies, see the docs on [strategyfiles](https://github.com/jerometwell/pynonymizer/blob/master/doc/strategyfiles.md)

### Examples

You can see strategyfile examples for existing database, such as wordpress or adventureworks sample database, in the the [examples folder](https://github.com/jerometwell/pynonymizer/blob/master/examples).

### Process outline

1. Restore from dumpfile to temporary database.
1. Anonymize temporary database with strategy.
1. Dump resulting data to file.
1. Drop temporary database.

If this workflow doesnt work for you, see [process control](https://github.com/jerometwell/pynonymizer/blob/master/doc/process-control.md) to see if it can be adjusted to suit your needs.

## Requirements
* Python >= 3.6

### mysql
* `mysql`/`mysqldump` Must be in $PATH
* Local or remote mysql >= 5.5
* Supported Inputs:
  * Plain SQL over stdout
  * Plain SQL file `.sql`
  * GZip-compressed SQL file `.gz` 
* Supported Outputs:
  * Plain SQL over stdout
  * Plain SQL file `.sql`
  * GZip-compressed SQL file `.gz` 
  * LZMA-compressed SQL file `.xz`

### mssql
* Requires extra dependencies: install package `pynonymizer[mssql]`
* MSSQL >= 2008
* Due to backup/restore limitations, you must be running pynonymizer on the *same server* as the database engine.
* Supported Inputs:
  * Local backup file
* Supported Outputs:
  * Local backup file

### postgres
* `psql`/`pg_dump` Must be in $PATH
* Local or remote postgres server
* Supported Inputs:
  * Plain SQL over stdout
  * Plain SQL file `.sql`
  * GZip-compressed SQL file `.gz` 
* Supported Outputs:
  * Plain SQL over stdout
  * Plain SQL file `.sql`
  * GZip-compressed SQL file `.gz` 
  * LZMA-compressed SQL file `.xz`

# Getting Started

## Usage
### CLI
1. Write a [strategyfile](https://github.com/jerometwell/pynonymizer/blob/master/doc/strategyfiles.md) for your database
1. See below:
```
usage: pynonymizer [-h] [--input INPUT] [--strategy STRATEGYFILE]
                   [--output OUTPUT] [--db-type DB_TYPE] [--db-host DB_HOST]
                   [--db-port DB_PORT] [--db-name DB_NAME] [--db-user DB_USER]
                   [--db-password DB_PASSWORD] [--fake-locale FAKE_LOCALE]
                   [--start-at STEP] [--skip-steps STEP [STEP ...]]
                   [--stop-at STEP] [--seed-rows SEED_ROWS]
                   [--mssql-backup-compression]
                   [--mysql-dump-opts MYSQL_DUMP_OPTS] [-v] [--verbose]
                   [--dry-run]

A tool for writing better anonymization strategies for your production
databases.

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        The source dump filepath to read from. Use `-` for
                        stdin. [$PYNONYMIZER_INPUT]
  --strategy STRATEGYFILE, -s STRATEGYFILE
                        A strategyfile to use during anonymization.
                        [$PYNONYMIZER_STRATEGY]
  --output OUTPUT, -o OUTPUT
                        The destination filepath to write the dumped output
                        to. Use `-` for stdout. [$PYNONYMIZER_OUTPUT]
  --db-type DB_TYPE, -t DB_TYPE
                        Type of database to interact with. More databases will
                        be supported in future versions. default: mysql
                        [$PYNONYMIZER_DB_TYPE]
  --db-host DB_HOST, -d DB_HOST
                        Database hostname or IP address.
                        [$PYNONYMIZER_DB_HOST]
  --db-port DB_PORT, -P DB_PORT
                        Database port. Defaults to provider default.
                        [$PYNONYMIZER_DB_PORT]
  --db-name DB_NAME, -n DB_NAME
                        Name of database to restore and anonymize in. If not
                        provided, a unique name will be generated from the
                        strategy name. This will be dropped at the end of the
                        run. [$PYNONYMIZER_DB_NAME]
  --db-user DB_USER, -u DB_USER
                        Database credentials: username. [$PYNONYMIZER_DB_USER]
  --db-password DB_PASSWORD, -p DB_PASSWORD
                        Database credentials: password. Recommended: use
                        environment variables to avoid exposing secrets in
                        production environments. [$PYNONYMIZER_DB_PASSWORD]
  --fake-locale FAKE_LOCALE, -l FAKE_LOCALE
                        Locale setting to initialize fake data generation.
                        Affects Names, addresses, formats, etc.
                        [$PYNONYMIZER_FAKE_LOCALE]
  --start-at STEP       Choose a step to begin the process (inclusive).
                        [$PYNONYMIZER_START_AT]
  --skip-steps STEP [STEP ...]
                        Choose one or more steps to skip.
                        [$PYNONYMIZER_SKIP_STEPS]
  --stop-at STEP        Choose a step to stop at (inclusive).
                        [$PYNONYMIZER_STOP_AT]
  --seed-rows SEED_ROWS
                        Specify a number of rows to populate the fake data
                        table used during anonymization.
                        [$PYNONYMIZER_SEED_ROWS]
  --mssql-backup-compression
                        [MSSQL] Use compression when backing up the database.
                        [$PYNONYMIZER_MSSQL_BACKUP_COMPRESSION]
  --mysql-dump-opts MYSQL_DUMP_OPTS
                        [MYSQL] pass additional arguments to the mysqldump
                        process (advanced use only!).
                        [$PYNONYMIZER_MYSQL_DUMP_OPTS]
  -v, --version         show program's version number and exit
  --verbose             Increases the verbosity of the logging feature, to
                        help when troubleshooting issues.
                        [$PYNONYMIZER_VERBOSE]
  --dry-run             Instruct pynonymizer to skip all process steps. Useful
                        for testing safely. [$PYNONYMIZER_DRY_RUN]

```
### Package
Pynonymizer can also be invoked programmatically / from other python code. See [pynonymizer/pynonymize.py](pynonymizer/pynonymize.py)

```python
from pynonymizer.pynonymize import pynonymize

# pynonymize is roughly equivalent to calling the main CLI
pynonymize(input_path="./backup.sql", strategyfile_path="./strategy.yml" [...] )
```