# `pynonymizer` [![pynonymizer on PyPI](https://img.shields.io/pypi/v/pynonymizer)](https://pypi.org/project/pynonymizer/) [![Downloads](https://static.pepy.tech/badge/pynonymizer)](https://pepy.tech/project/pynonymizer) ![License](https://img.shields.io/pypi/l/pynonymizer)

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

Pynonymizer's main data replacement mechanism `fake_update` is a random selection from a small pool of data (`--seed-rows` controls the available Faker data). This process is chosen for compatibility and speed of operation, but does not guarantee uniqueness. 
This may or may not suit your exact use-case. For a full list of data generation strategies, see the docs on [strategyfiles](https://github.com/rwnx/pynonymizer/blob/main/doc/strategyfiles.md)

### Examples

You can see strategyfile examples for existing database, such as wordpress or adventureworks sample database, in the the [examples folder](https://github.com/rwnx/pynonymizer/blob/main/examples).

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

### Package
Pynonymizer can also be invoked programmatically / from other python code. See the module entrypoint [pynonymizer](pynonymizer/__init__.py) or [pynonymizer/pynonymize.py](pynonymizer/pynonymize.py)

```python
import pynonymizer

pynonymizer.run(input_path="./backup.sql", strategyfile_path="./strategy.yml" [...] )
```
