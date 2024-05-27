# `pynonymizer` [![pynonymizer on PyPI](https://img.shields.io/pypi/v/pynonymizer)](https://pypi.org/project/pynonymizer/) [![Downloads](https://static.pepy.tech/badge/pynonymizer)](https://pepy.tech/project/pynonymizer) ![License](https://img.shields.io/pypi/l/pynonymizer)

# pynonymizer

pynonymizer is a tool for anonymizing sensitive production database dumps, allowing you to create realistic test datasets while maintaining GDPR/Data Protection compliance. It replaces personally identifiable information (PII) in your database with random, yet realistic data, using the Faker library and other functions.

Key features:

- Supports MySQL, PostgreSQL, and MSSQL databases
- Accepts various input formats (SQL, compressed files)
- Generates anonymized output in multiple formats
- Flexible data generation strategies for different use cases
- Easy to use command-line interface and Python library

With pynonymizer, you can safely share production database copies with developers and testers, enabling better staging environments, integration tests, and database migration simulations, without compromising user privacy.


## How does it work?
`pynonymizer` replaces personally identifiable data in your database with **realistic** pseudorandom data, from the `Faker` library or from other functions.
There are a wide variety of data types available which should suit the column in question, for example:

* `unique_email`
* `company`
* `file_path`
* `[...]`

Pynonymizer's main data replacement mechanism `fake_update` is a random selection from a small pool of data (`--seed-rows` controls the available Faker data). This process is chosen for compatibility and speed of operation, but does not guarantee uniqueness. 
This may or may not suit your exact use-case. For a full list of data generation strategies, see the docs on [strategyfiles](https://github.com/rwnx/pynonymizer/blob/main/doc/strategyfiles.md)

### Examples

You can see strategyfile examples for existing databases, in the the [examples folder](https://github.com/rwnx/pynonymizer/blob/main/examples).

### Process outline

1. Restore from dumpfile to temporary database.
1. Anonymize temporary database with strategy.
1. Dump resulting data to file.
1. Drop temporary database.

If this workflow doesnt work for you, see [process control](https://github.com/rwnx/pynonymizer/blob/main/doc/process-control.md) to see if it can be adjusted to suit your needs.

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
* For `RESTORE_DB`/`DUMP_DB` operations, the database server *must* be running
  locally with pynonymizer. This is because MSSQL `RESTORE` and `BACKUP` instructions
  are received by the database, so piping a local backup to a remote server is not possible.
* The anonymize process can be performed on remote servers, but you are responsible for creating/managing the target database.
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
1. Write a [strategyfile](https://github.com/rwnx/pynonymizer/blob/main/doc/strategyfiles.md) for your database
1. Check out the help for a description of options `pynonymizer --help`
1. Start Anonymizing!

### Docker

![Docker Image Version](https://img.shields.io/docker/v/rwnxt/pynonymizer?label=Docker)


pynonymizer is available as a docker image so that you dont have to install the client tools for your database. 

See https://hub.docker.com/repository/docker/rwnxt/pynonymizer

```sh
# As pynonymizer depends on strategyfiles, you'll need to create a file mount so the file can be read.
docker run --mount type=bind,source=./strategyfile.yml,target=/tmp/strategyfile.yml rwnxt/pynonymizer -s /tmp/strategyfile.yml --db-host [...]
```

### Package
Pynonymizer can also be invoked programmatically / from other python code. See the module entrypoint [pynonymizer](pynonymizer/__init__.py) or [pynonymizer/pynonymize.py](pynonymizer/pynonymize.py)

```python
import pynonymizer

pynonymizer.run(input_path="./backup.sql", strategyfile_path="./strategy.yml" [...] )
```
