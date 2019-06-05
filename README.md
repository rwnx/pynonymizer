# pynonymizer

pynonymizer is a tool for translating sensitive production database dumps into anonymized copies.

This anonymized data can be used in development and testing.
## Supported Databases
1. mysql

## Requirements
### mysql
* `mysql`
* `mysqldump`
* database connection (to restore, anonymize, and dump from)
* access to mysqldump file (single file)

## Process
1. Restore database from dumpfile
1. anonymize database with appropriate strategy
1. dump resulting data to file
1. clean up!

# Getting Started

## Usage
1. Set required env (normally, or using dotenv)
1. Write a [strategyfile](/doc/strategyfiles.md) for your database
1. Run command `pynonymizer`
```
usage: pynonymizer [-h] [--db-name DB_NAME] [-v] input strategyfile output

A tool for writing better anonymization strategies for your production databases.

environment variables:
  DB_TYPE      Type of database (mysql)
  DB_HOST      Database host/ip (127.0.0.1)
  DB_USER      Database username
  DB_PASS      Database password
  FAKE_LOCALE  Locale to initialize faker generation (en_GB)

positional arguments:
  input                 The source dumpfile to read from.

                        [.sql, .gz]
  strategyfile          A strategyfile to use during anonymization.
  output                The destination to write the dumped output to.
                        [.sql, .gz]

optional arguments:
  -h, --help            show this help message and exit
  --db-name DB_NAME, -n DB_NAME
                        Name of database to create in the target host and restore to. This will default to a random name.
  -v, --version         show program's version number and exit
```

## Development
1. setup venv
2. install dependencies with `pip install -r requirements.txt`

### Testing
1. run `tox`


## License

[MIT](LICENSE)
