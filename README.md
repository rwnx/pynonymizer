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


## Development
1. setup venv
1. copy `.env` for your environment
2. install dependencies with `pip install -r requirements.txt`
