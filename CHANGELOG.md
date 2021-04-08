# Changelog
This document lists the changes between release versions.

These are user-facing changes. To see the changes in the code between versions you can compare git tags.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Types of changes
  * `Added` for new features.
  * `Changed` for changes in existing functionality.
  * `Deprecated` for soon-to-be removed features.
  * `Removed` for now removed features.
  * `Fixed` for any bug fixes.
  * `Security` in case of vulnerabilities.

  -------------------------------------------------------------------
## [Unreleased]
- Added Integration tests for MSSQL
- Added Driver auto-selection for MSSQL. This should find the correct driver on different systems. Where multiple drivers are detected a warning will be issued, and the first driver will be selected. To override this behaviour, you can specify the driver manually using cli opt `--mssql-driver / $PYNONYMIZER_MSSQL_DRIVER`
- Changed Integration tests to show cmd output better in CI.
- Fixed an issue in MSSQL where anonymization would be deterministically applied to all rows the same instead of distributed.
- Changed MSSQL connection behaviour: provider will now allow truncation using `ANSI_WARNINGS off;` when updating tables.
- Fixed a typo in mssql, mysql and postgres when running strategy before/after scripts.

## [1.17.0] 2021-03-29
- Added New _additional-opts_ style parameters which allow you to control the behaviour of the underlying dump and restore tools more effectively.
  `*-cmd-opts` will be appended to the batched restore subprocess, while `*-dump-opts` will be appended to the dump (pgdump, mysqldump) subprocess
  These are advanced features and can seriously modify or even break the behaviour of pynonymizer. Use with caution!
  * `--mysql-cmd-opts/$PYNONYMIZER_MYSQL_CMD_OPTS`
  * `--postgres-cmd-opts/$PYNONYMIZER_POSTGRES_CMD_OPTS`
  * `--postgres-dump-opts/$PYNONYMIZER_POSTGRES_DUMP_OPTS`
- Fixed a bug where `$PYNONYMIZER_VERBOSE` was not being detected correctly.
- Changed order of `additional_args` for Mysql dump runner, so additional options are added _after_ the existing args.
- Added cli warnings for deprecated positional arguments and environmental variables.
- Added Python 3.9 to official support description(pypi) and unit test targets.

## [1.16.0] 2021-03-16
- Added support for LZMA `*.xz` compression on file output. To use this feature, Specify an output path ending with `.xz`.
- Minor improvements to internal test suite.

## [1.15.0] 2021-01-29
- Added main function `run` exposure to `pynonymizer` package.
  Check out pynonymizer/pynonymize.py for more usage information
  ```python
  from pynonymizer import run
  ```
- Added more documentation to reflect usage & project features.
- Exclude `tests/` directory from pip package.

## [1.14.0] 2020-12-07
- Added `fake_update` Strategy feature: `sql_type`: Choose an sql datatype to cast to when anonymizing values. The new value will be cast to the chosen datatype.
- Fixed PostgreSQL column escaping. Keywords like `SELECT`, `FROM` or `WHERE` can now be used in strategy files.

## [1.13.0] 2020-10-22
- Added new table strategy `DELETE`, which should delete _with_ checks (e.g. foreign keys) on most providers. 

## [1.12.0] 2020-09-25
- Added ability to pipe output to/from pynonymizer from stdout, using `-` in place of the input/output arguments. This functionality is available for mysql and postgres providers.

  This means you can now use pynonymizer as part of a pipeline with other tools, e.g. 
  ```
  mysqldump [...] | pynonymizer -i - -o - | aws s3 cp - s3://bucket/aws-test.tar.gz 
  ```
- Changed default logging output to stderr. This is to facilitate stdin/out being used for data.
- Removed production logging feature in favour of stderr/out logging. Logging to files will no longer by considered pynonymizer's concern.

## [1.11.2] 2020-09-23
- Changed package metadata to improve PyPI presence.

## [1.11.1] 2020-08-29
- Fixed an incorrectly labelled version string: `1.11.10`. Re-releasing under this version.

## [1.11.0] 2020-08-29
- Changed mysql provider to include an arbitrary delay after anonymize_db, to prevent
  interference with transactional dump `mysqldump` calls. 
- Removed the database connection pre-test as its use suggests conditions about the database
  that are not present in all circumstances with all providers. Pynonymizer will no longer test a connection as part of a dry-run. 

## [1.10.1] 2020-07-22
- Fixed a confusing note in the README.md that was introduced accidentally

## [1.10.0] 2020-07-22
- Added `--mysql-dump-opts`/ `$PYNONYMIZER_MYSQL_DUMP_OPTS` to allow custom command overrides to the mysqldump process.
- Fixed a bug where complex arguments to faker could cause an invalid seed table column name to be generated.

## [1.9.0] 2020-06-25
- Fixed a bug where using no fake_update columns would cause an error
- Changed Documentation for `fake_update` strategies to remove an erroneous example type.

## [1.8.0] 2020-01-17
- Added `--dry-run` / `$PYNONYMIZER_DRY_RUN` option to run all the non-destructive fail-fast options without fear of actual process execution.
- Fixed a bug in mysql provider where using the default unspecified port would cause an error.
- Fixed a bug in postgres provider where seed_rows was being ignored.
- Fixed a bug in the Postgres provider that would cause all rows to be updated with the same 'random' value.
- Fixed a bug in mysql/postgres providers that would cause before/after scripts to fail to run.

## [1.7.0] 2020-01-10
- Added option `--db-port`/`-P`/`$PYNONYMIZER_DB_PORT` to specify your database provider's connection port.
- Added option `--verbose` to increase the verbosity of the logging feature. Currently, this is used to log more info
  from a database error, but more areas will be included in future.

## [1.6.2] 2019-09-17
- Fixed a mysql provider issue: in MariaDB, multiple string columns in a strategy could cause a row length error when constructing the seed table.

## [1.6.1] 2019-08-02
- Fixed a bug where static code relying on pyodbc would cause a ModuleNotFoundError

## [1.6.0] 2019-08-02
- Changed mssql support to an package extra. If mssql support is required, install extra `pynonymizer[mssql]`.
- Added errors for mssql ODBC installation issues, missing extras.
- Added support for linux paths in MSSQL backup file moves/restore.
- Added support for postgres (subprocess-based psql/pg_dump): use `--db-type/-t postgres`
- Fixed typo in mssql dependency error (local server required).

## [1.5.0] 2019-07-13
- Added Support for different strategyfile formats: `.json`/`.yaml`/`.yml`
- Added option `--seed-rows`: specify the seed row size for fake data generated.
- Added MSSQL provider: use `--db-type/-t mssql`
- Added MSSQL option `---mssql-backup-compression` and added convention for provider-specific arguments (prefixed by `dbtype-`)
- Added optional table strategy key: `schema`. For supported databases (mssql), you can now specify the schema of the table strategy.
- Added strategy parsing mode for multi-table and multi-column updates of the same table/column names
- Changed mandatory arguments for main process to account for different process step permutations:
    - input is optional if `RESTORE_DB` is skipped
    - strategyfile is optional if `ANONYMIZE_DB` is skipped
    - output is optional if `DUMP_DB` is skipped
    - db_name is mandatory if a step prevents it from being determined automatically e.g. strategyfile is missing

## [1.4.1] 2019-06-29
 - Fixed an issue where import syntax was preventing certain modules from being loaded in python 3.6

## [1.4.0] 2019-06-23
- Added **all** faker providers to the `fake_update` type.
- Added `fake_args` kwargs key to the `fake_update` type. You can now make use of parameterized providers in faker!
- Added "verbose-style" strategy format to complement original shorthand autodetection.
- Added `where` option for where-clause support on all update_column strategies. Columns with a matching where option are grouped together for execution.
- Added Stock strategies for sylius and wordpress 4.4 in the main repository.
- Added column strategy: `literal` for setting literal values e.g. `RAND()`, `'A String'`
- Changed parsing for mapping column strategy keys to classes: Parser no longer ignored unused keys


## [1.3.0] 2019-06-17
- Fixed some minor spelling errors in the help text.
- Fixed an issue where dumping an empty database(unlikely, but still possible) could cause an unhandled exception.
- Changed the way mysql provider handles execution so CalledProcessErrors no longer expose all command parameters by default.
- Added `scripts` strategyfile section. you can now specify `before` and `after` scripts to be run decorating the anonymization process. (see doc/strategyfiles.md)
- Added Process steps, e.g. `CREATE_DB`, `ANONYMIZE_DB` for improved logging and skip behaviour (see doc/process-control.md)
- Added process control options:
    - `--start-at STEP`: choose a step to start at (inclusive)
    - `--stop-at STEP`: choose a step to stop at (inclusive)
    - `--skip-steps STEP [..STEP]` : specify one or more steps to skip in the process

## [1.2.0] 2019-06-14
 - Added new environment variables, optionals for all arguments. See the help `pynonymizer -h` for more information
 - Changed Internal structure to assist with better testing.
 - Deprecated positional arguments. These will no longer appear in helptext and are not required. You can now use all-environmental, all-optional or a mix of both.
 Going forward, The preferred solution is `--optional-vars` or environment variables.
 - Deprecated old environment variables in favour of new prefix `PYNONIMIZER_`.
 These will continue to work but will be removed in a future release.
    - `DB_TYPE -> PYNONYMIZER_DB_TYPE`
    - `DB_HOST -> PYNONYMIZER_DB_HOST`
    - `DB_NAME -> PYNONYMIZER_DB_NAME`
    - `DB_USER -> PYNONYMIZER_DB_USER`
    - `DB_PASS -> PYNONYMIZER_DB_PASSWORD`
    - `FAKE_LOCALE -> PYNONYMIZER_FAKE_LOCALE`

## [1.1.2] 2019-06-08
 - Added `-v` `--version` flag argument. [#4]
 - Added additional metadata to `setup.py` for better PyPI info. [#3]

## [1.0.0] 2019-06-04
 - Package Release - Hooray!
