# pynonymizer

pynonymizer is a tool for translating sensitive production database dumps into anonymized copies.

This anonymized data can be used in development and testing.

## Requirements
1. `mysql`, `mysqldump`, database connection 

A database connection is required to restore the database to during the anonymization process.

## Process
1. Restore database from dumpfile
1. anonymize database with appropriate strategy
1. dump resulting data to file
1. clean up!

## Installation
1. Install `python setup.py install`

## Usage
1. Install
1. Set env vars using .env or other method
1. run command `pynonymizer`
```
usage: pynonymizer [-h] input_location strategyfile output_location

positional arguments:
  input_location   The source dumpfile to read from
  strategyfile     a strategyfile to use during anonymization (e.g.
                   example.yml)
  output_location  The destination to write the output to

optional arguments:
  -h, --help       show this help message and exit
```


## Development
1. setup venv
1. copy `.env` for your environment
2. install dependencies with `pip install -r requirements.txt`
