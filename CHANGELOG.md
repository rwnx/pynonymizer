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
- Changed mssql support to an package extra. If mssql support is required, install extra `pynonymizer[mssql]`
- Added errors for mssql ODBC installation issues, missing extras

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
