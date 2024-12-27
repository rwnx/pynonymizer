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

## [2.5.0] 2024-12-27
## Fixed
- Fixed an issue where postgres seed table was using invalid datatype `DATETIME`. changed to `TIMESTAMP`
- Fixed a issue when updates to MSSQL data would result in multiple messages coming back from the server, e.g. when triggers update multiple tables and NOCOUNT is OFF. Another scenario is before or after scripts that call stored procs wth PRINT statements in them or that return multiple resultsets before completing. Without the fix, this issue can result in tables only partially anonymized.
- Fix error messages when running MSSQL anonymization with --verbose enabled

## [2.4.0] 2024-07-30
## Changed
- pynonymizer CLI will now catch errors and log them instead of dumping the stacktrace.

## Fixed
- Fixed a bug where MSSQL provider would override the server connection with (local). 
- Fixed a bug where failing dump & restore operations would not be caught by pynonymizer. Pynonymizer will now error when mysql/mysqldump or psql/pgdump returns an error code.

## [2.3.1] 2024-05-27
## Fixed
- Fixed an issue with the release workflow for the docker deployment.

## [2.3.0] 2024-05-27
## Fixed
- Fixed a bug where verbose logging was not lowering the log level correctly

## Added
- Logging output will now be colored according to level
- Added debug log: sql statements to mssql, mysql, postgres providers
- Added debug log: connection string log to mssql

## [2.2.1] 2024-04-30
## Fixed
- Fixed a bug where command line switches were not named correctly. `--mysql-cmd-opts` and `--mssql-backup-compression` were duplicated, making some options difficult to access.
- Error codes from the CLI were not working correctly. Pynonymizer will now report failure on validations and other errors.
- Fixed a bug where some environment variables were changed. Both variations will now be supported to ease migration.
  - `PYNONYMIZER_START_AT`, `PYNONYMIZER_START_AT_STEP`, 
  - `PYNONYMIZER_STOP_AT`, `PYNONYMIZER_STOP_AT_STEP`,
  - `PYNONYMIZER_STRATEGY`, `PYNONYMIZER_STRATEGYFILE`
  
## [2.2.0] 2024-04-14
### Added
- pynonmizer now has docker images with the database client and dependencies built in. These are in beta, please report any issues to the github. 
See https://hub.docker.com/r/rwnxt/pynonymizer 

### Changed
- mssql now sets Mars_Connection=Yes on connection as this allows support for threading without connection busy.

## [2.1.1] 2024-04-06
### Fixed
- Fixed a bug where `--skip-steps` would be ignored if passed via the CLI. [#152]

## [2.1.0] 2024-04-03
### Added
- `--workers` option to control number of threads to use when anonymizing. Table anonymization will be done in threads and should result in a major speed boost. By default, a single worker is used.
- `--mssql-ansi-warnings-off` option (default: on) to disable ansi warnings when making updates

### Fixed
- Fixed a bug where using the raw `pynonymizer` command would cause an unexpected error.

## [2.0.0] 2024-03-28
### Added
- Better error messages for unsupported fake types - the error should now explain the problem and link to the docs in the right section. [#133]
- Error message for when a fake_type is used with the wrong config kwargs (these would have previously been caught under "unsupported fake types")
- event hooks for progress events. you can now use your own progress bar if you're invoking the process via the python interface.
- support for connection strings in mssql. 

### Changed
- removed credentials validation (db_user, db_password) from the initial cli validation, as these are now handled by your original database. This should grant the most flexibility for different types of credentials.

### Removed
- Positional INPUT. Use the -i/--input option instead
- Positional STRATEGYFILE. Use the -s/--strategy option instead
- Positional OUTPUT. Use the -o/--output option instead
- Deprecated environment keys: `DB_TYPE, DB_HOST, DB_NAME, DB_USER, DB_PASS`.
- `--fake-locale` `-l` `$PYNONYMIZER_FAKE_LOCALE` cli option. Use the `locale:` key in your strategyfile instead
- `dotenv` is no longer a dependency. you are expected to load your environment variables yourself!
- Removed local server check for mssql, as manual overrides using connection string will be possible. pynonymizer isn't going to stop you!

## [1.25.0] 2023-03-29
### Changed
- Postgres FAKE_UPDATE strategy now uses an id-based randomization to pick from the seed table. 
  This speeds up updates on large tables, as the seed table no longer needs to be ordered for every row in the target table.
  Also this makes performances less dependent on the length of the seed table.

## [1.24.0] 2022-09-07
### Changed
- In MySQL,`db_host`, `db_user`, `db_pass` and `db_port` are now optional and will be omitted from CLI options if not passed.
  You can now use the `my.cnf` file to pass config to the mysql CLI. [#108]. Read more about the rationale behind these changes in [doc/database-credentials.md](doc/database-credentials.md).
- In Postgres, `db_pass` will be optional and will be omitted from CLI options if not passed. You can now use the `.pgpass` file to securely pass the password to the pg CLI. Read more about the rationale behind these changes in [doc/database-credentials.md](doc/database-credentials.md).

## [1.23.0] 2022-08-22
### Added
- Added offical test support for python 3.10
- Added a new option, `--ignore-anonymization-errors` that will allow the anonymization step to error without propagating errors upstream. This is useful if you always want the resulting dumpfile, even when there are db or schema faults. 
### Changed
- Changed how seed rows are assigned their default value and made sure this value made it's way into the documentation (150 rows by default).
### Deprecated
- Column Strategy "empty" has been deprecated because its effect was inconsistent on different providers and column types.
  using it will generate a warning on config parse. It has been removed from the documentation so as to cut down on confusion.
  The recommended way to update a column to empty is to use a `literal` set to the appropriate "empty" data for the column.
### Removed
- Removed offical test support for python 3.6
- Removed process step `GET_SOURCE`(no-op) as it was causing confusion. This is not considered a breaking change as it was never implemented.

## [1.22.0] 2022-02-06
### Changed
- Changed anonymization process to attempt to anonymize all tables before throwing errors. [#96]
### Fixed
- Fixed a bug in mysql/postgres that didn't wait for the restore dump process to complete before starting the anonymize procedure

## [1.21.3] 2021-11-14
### Added
- Added a workflow that automatically runs `black` on incoming PRs, to set a canonical standard for formatting in the project.
### Fixed
- Fixed a bug in mysql/postgres where stdin is not closed after reading

## [1.21.2] 2021-09-06
### Fixed
- Fixed a bug in the config parser where literal column strategies that contained `type` threw an error

## [1.21.1] 2021-06-22
### Fixed
- Fixed a bug in the config parser that would always override the locale with either the cli argument or the fallback

## [1.21.0] 2021-05-31
### Added
- Added Custom Providers to strategyfiles. You can now include custom Faker providers in your
  strategyfiles, using the `providers` top-level key.
- Added Locale key `locale`(top-level) to strategyfiles. This is designed to replace the `-l`/`--fake-locale` CLI option. 
### Deprecated
- Deprecated `-l`/`--fake-locale` option. You should use the `locale` key in your strategyfile. 
  This will be removed in a future release.
### Fixed
- Fixed a bug in postgres where table and column names were not consistently escaped. 
- Fixed some documentation errors.

## [1.20.0] 2021-05-06
### Fixed
- Fixed a bug where postgres tables could not be anonymized if they contained a json or jsonb column.

## [1.19.0] 2021-04-24
### Added
- Added a new compact syntax for column strategy `literal`. Surrounding your value in parentheses `()` will select the literal strategy. 
- Added new cli option `--only-step` to select a step to run. Useful for running anonymization routines without having to use start-at and stop-at simultaneously. e.g. `--only-step ANONYMIZE_DB`. 

### Changed
- Improvements to mssql driver auto-selection process, to attempt to select a more recent driver by default.
### Fixed
- Fixed a bug where on a system with no ODBC drivers, an incorrect error would be thrown.

## [1.18.1] 2021-04-12
### Fixed
- Fixed a fatal error when deprecated environment vars were used (See 1.2.0 notes for a full list).

## [1.18.0] 2021-04-11
### Added
- Added Integration tests for MSSQL
- Added Driver auto-selection for MSSQL. This should find the correct driver on different systems. Where multiple drivers are detected a warning will be issued, and the first driver will be selected. To override this behaviour, you can specify the driver manually using cli opt `--mssql-driver / $PYNONYMIZER_MSSQL_DRIVER`
- Added support for remote servers in MSSQL, provided RESTORE_DB/DUMP_DB is not being used. 
- Added support for MSSQL servers using custom ports.
### Changed
- Changed Integration tests to show cmd output better in CI.
- Changed MSSQL connection behaviour: provider will now allow truncation using `ANSI_WARNINGS off;` when updating tables.
- Changed verbose-mode behaviour to include more information via debug logs during CLI runs.
### Fixed
- Fixed an issue in MSSQL where anonymization would be deterministically applied to all rows the same instead of distributed.
- Fixed a typo in mssql, mysql and postgres when running strategy before/after scripts.
## [1.17.0] 2021-03-29
### Added
- Added New _additional-opts_ style parameters which allow you to control the behaviour of the underlying dump and restore tools more effectively.
  `*-cmd-opts` will be appended to the batched restore subprocess, while `*-dump-opts` will be appended to the dump (pgdump, mysqldump) subprocess
  These are advanced features and can seriously modify or even break the behaviour of pynonymizer. Use with caution!
  * `--mysql-cmd-opts/$PYNONYMIZER_MYSQL_CMD_OPTS`
  * `--postgres-cmd-opts/$PYNONYMIZER_POSTGRES_CMD_OPTS`
  * `--postgres-dump-opts/$PYNONYMIZER_POSTGRES_DUMP_OPTS`
- Added cli warnings for deprecated positional arguments and environmental variables.
- Added Python 3.9 to official support description(pypi) and unit test targets.
### Changed
- Changed order of `additional_args` for Mysql dump runner, so additional options are added _after_ the existing args.
### Fixed
- Fixed a bug where `$PYNONYMIZER_VERBOSE` was not being detected correctly.
## [1.16.0] 2021-03-16
### Added
- Added support for LZMA `*.xz` compression on file output. To use this feature, Specify an output path ending with `.xz`.
### Changed
- Minor improvements to internal test suite.
## [1.15.0] 2021-01-29
### Added
- Added main function `run` exposure to `pynonymizer` package.
  Check out pynonymizer/pynonymize.py for more usage information
  ```python
  from pynonymizer import run
  ```
- Added more documentation to reflect usage & project features.
### Changed
- Exclude `tests/` directory from pip package.

## [1.14.0] 2020-12-07
### Added
- Added `fake_update` Strategy feature: `sql_type`: Choose an sql datatype to cast to when anonymizing values. The new value will be cast to the chosen datatype.
### Fixed
- Fixed PostgreSQL column escaping. Keywords like `SELECT`, `FROM` or `WHERE` can now be used in strategy files.

## [1.13.0] 2020-10-22
### Added
- Added new table strategy `DELETE`, which should delete _with_ checks (e.g. foreign keys) on most providers. 

## [1.12.0] 2020-09-25
### Added
- Added ability to pipe output to/from pynonymizer from stdout, using `-` in place of the input/output arguments. This functionality is available for mysql and postgres providers.

  This means you can now use pynonymizer as part of a pipeline with other tools, e.g. 
  ```
  mysqldump [...] | pynonymizer -i - -o - | aws s3 cp - s3://bucket/aws-test.tar.gz 
  ```
### Changed
- Changed default logging output to stderr. This is to facilitate stdin/out being used for data.
### Removed
- Removed production logging feature in favour of stderr/out logging. Logging to files will no longer by considered pynonymizer's concern.

## [1.11.2] 2020-09-23
### Changed
- Changed package metadata to improve PyPI presence.

## [1.11.1] 2020-08-29
### Fixed
- Fixed an incorrectly labelled version string: `1.11.10`. Re-releasing under this version.

## [1.11.0] 2020-08-29
### Changed
- Changed mysql provider to include an arbitrary delay after anonymize_db, to prevent
  interference with transactional dump `mysqldump` calls. 
### Removed
- Removed the database connection pre-test as its use suggests conditions about the database
  that are not present in all circumstances with all providers. Pynonymizer will no longer test a connection as part of a dry-run. 

## [1.10.1] 2020-07-22
### Changed
- Fixed a confusing note in the README.md that was introduced accidentally

## [1.10.0] 2020-07-22
### Added
- Added `--mysql-dump-opts`/ `$PYNONYMIZER_MYSQL_DUMP_OPTS` to allow custom command overrides to the mysqldump process.
### Fixed
- Fixed a bug where complex arguments to faker could cause an invalid seed table column name to be generated.

## [1.9.0] 2020-06-25
### Fixed
- Fixed a bug where using no fake_update columns would cause an error
### Changed
- Changed Documentation for `fake_update` strategies to remove an erroneous example type.

## [1.8.0] 2020-01-17
### Added
- Added `--dry-run` / `$PYNONYMIZER_DRY_RUN` option to run all the non-destructive fail-fast options without fear of actual process execution.
### Fixed
- Fixed a bug in mysql provider where using the default unspecified port would cause an error.
- Fixed a bug in postgres provider where seed_rows was being ignored.
- Fixed a bug in the Postgres provider that would cause all rows to be updated with the same 'random' value.
- Fixed a bug in mysql/postgres providers that would cause before/after scripts to fail to run.

## [1.7.0] 2020-01-10
### Added
- Added option `--db-port`/`-P`/`$PYNONYMIZER_DB_PORT` to specify your database provider's connection port.
- Added option `--verbose` to increase the verbosity of the logging feature. Currently, this is used to log more info
  from a database error, but more areas will be included in future.

## [1.6.2] 2019-09-17
### Fixed
- Fixed a mysql provider issue: in MariaDB, multiple string columns in a strategy could cause a row length error when constructing the seed table.

## [1.6.1] 2019-08-02
### Fixed
- Fixed a bug where static code relying on pyodbc would cause a ModuleNotFoundError

## [1.6.0] 2019-08-02
### Added
- Added errors for mssql ODBC installation issues, missing extras.
- Added support for linux paths in MSSQL backup file moves/restore.
- Added support for postgres (subprocess-based psql/pg_dump): use `--db-type/-t postgres`
### Changed
- Changed mssql support to an package extra. If mssql support is required, install extra `pynonymizer[mssql]`.
### Fixed
- Fixed typo in mssql dependency error (local server required).

## [1.5.0] 2019-07-13
### Added
- Added Support for different strategyfile formats: `.json`/`.yaml`/`.yml`
- Added option `--seed-rows`: specify the seed row size for fake data generated.
- Added MSSQL provider: use `--db-type/-t mssql`
- Added MSSQL option `---mssql-backup-compression` and added convention for provider-specific arguments (prefixed by `dbtype-`)
- Added optional table strategy key: `schema`. For supported databases (mssql), you can now specify the schema of the table strategy.
- Added strategy parsing mode for multi-table and multi-column updates of the same table/column names
### Changed
- Changed mandatory arguments for main process to account for different process step permutations:
    - input is optional if `RESTORE_DB` is skipped
    - strategyfile is optional if `ANONYMIZE_DB` is skipped
    - output is optional if `DUMP_DB` is skipped
    - db_name is mandatory if a step prevents it from being determined automatically e.g. strategyfile is missing

## [1.4.1] 2019-06-29
### Fixed
 - Fixed an issue where import syntax was preventing certain modules from being loaded in python 3.6

## [1.4.0] 2019-06-23
### Added
- Added **all** faker providers to the `fake_update` type.
- Added `fake_args` kwargs key to the `fake_update` type. You can now make use of parameterized providers in faker!
- Added "verbose-style" strategy format to complement original shorthand autodetection.
- Added `where` option for where-clause support on all update_column strategies. Columns with a matching where option are grouped together for execution.
- Added Stock strategies for sylius and wordpress 4.4 in the main repository.
- Added column strategy: `literal` for setting literal values e.g. `RAND()`, `'A String'`
### Changed
- Changed parsing for mapping column strategy keys to classes: Parser no longer ignored unused keys


## [1.3.0] 2019-06-17
### Added
- Added `scripts` strategyfile section. you can now specify `before` and `after` scripts to be run decorating the anonymization process. (see doc/strategyfiles.md)
- Added Process steps, e.g. `CREATE_DB`, `ANONYMIZE_DB` for improved logging and skip behaviour (see doc/process-control.md)
- Added process control options:
    - `--start-at STEP`: choose a step to start at (inclusive)
    - `--stop-at STEP`: choose a step to stop at (inclusive)
    - `--skip-steps STEP [..STEP]` : specify one or more steps to skip in the process
### Changed
- Changed the way mysql provider handles execution so CalledProcessErrors no longer expose all command parameters by default.
### Fixed
- Fixed some minor spelling errors in the help text.
- Fixed an issue where dumping an empty database(unlikely, but still possible) could cause an unhandled exception.

## [1.2.0] 2019-06-14
### Added
 - Added new environment variables, optionals for all arguments. See the help `pynonymizer -h` for more information
### Changed
 - Changed Internal structure to assist with better testing.
### Deprecated
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
### Added
 - Added `-v` `--version` flag argument. [#4]
 - Added additional metadata to `setup.py` for better PyPI info. [#3]

## [1.0.0] 2019-06-04
 - Package Release - Hooray!
