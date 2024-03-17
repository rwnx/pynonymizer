# Process Control

pynonymizer may be useful to you as a complete process or in part. 
For example, you might not want the database to be dropped at the end of the process, so you can query it later.

Pynonymize offers a few of options for controlling the process. 

```
  --start-at STEP       Choose a step to begin the process (inclusive).
                        [$PYNONYMIZER_START_AT]
  --skip-steps STEP [STEP ...]
                        Choose one or more steps to skip.
                        [$PYNONYMIZER_SKIP_STEPS]
  --stop-at STEP        Choose a step to stop at (inclusive).
                        [$PYNONYMIZER_STOP_AT]
  --only-step STEP      Choose one step to perform.
                        [$PYNONYMIZER_ONLY_STEP]
```

## Steps
Pynonymizer's process is broken into steps:
  - `START`: NOOP action, first
  - `CREATE_DB`: Create the named database
  - `RESTORE_DB`: Restore the database from input 
  - `ANONYMIZE_DB`: Run the anonymization process
  - `DUMP_DB`: Dump the database to output
  - `DROP_DB`: Drop the named database
  - `END`: NOOP, last

## Control
Essentially: steps can be run, or they can be skipped. 

There are a few ways a step can be skipped:
  - `--start-at` is set to a value *after* the current step
  - `--stop-at` is set to a step *before* the current step
  - `--skip-steps` includes the current step
  - `--only-step` does *not* include the current step.
  
 If a step is skipped it will be logged as a warning, but the process will complete successfully as long as the remaining steps do.
 
## Examples
* Keep a database afer anonymization: `pynonymizer [...] --stop-at DUMP_DB`
* Anonymize `pynonymizer [...] --db-name sakila --only-step ANONYMIZE_DB`
* Restore `pynonymizer [...] --db-name sakila --only-step RESTORE_DB`
