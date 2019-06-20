# Strategyfiles 

Strategyfiles are YAML configurations containing the "What" and the "How" of the anonymization process *for a database*. 

pynonymizer can parse a strategyfile into a `DatabaseStrategy`, which will be used as a set of instructions during an anonymization run.

```yaml
tables:
  accounts:
    columns:
      password: empty
      current_sign_in_ip: ipv4_public
      last_sign_in_ip: ipv4_public
      username: user_name
      email:
        type: fake_update
        fake_type: company_email
        where: username != 'admin'
  transactions: truncate
  other_important_table: truncate
scripts:
  before:
    - DELETE FROM config where name = 'secret';
```

# Philosophy
Wherever there are multiple options for a key, such as a table or update_column strategy, the "verbose" syntax will be a dict, containing a `type` key that specifies the type of configuration.

```yaml
tables:
    table_example:
        type: table_type
        # [...]
```
In certain circumstances, the `type` key can be determined automatically by the content. For example, when a column key is set to `unique_login`, the type is automatically detected to be the `unique_login`, rather than a `fake_update` type with `fake_type: unique_login`.

When the `type` is automatically determined, this is called the "compact" syntax. 

The compact syntax has significantly fewer options but allows you to build many common configurations quickly and easily. 

# Syntax

## Key: `tables`
Tables is a top-level key, containing a subkey for each `table_name:table_strategy`pair.

Each table has an individual strategy.
* `truncate`
* `update_columns`

### Table Strategy: `truncate`
Wipe the entire table, preferably using a truncate statement.
```yaml
table_name: 
  type: truncate
    
# Compact Syntax:
table_name: truncate
```
### Table Strategy: `update_columns`
Overwrite columns in the table with specific or randomized values. 
```yaml
table_name:
  type: update_columns
  columns:
    column_name1: empty
    #[...]
  
# Compact Syntax: `type` can be omitted if `columns` key is present
table_name:
  columns:
    column_name1: empty
    #[...]
```
#### `where`
```yaml
column_name:
    type: empty
    where: username = 'barry'
```
All update_column types support a `where` key, that can be used to add conditions to updates. This is only available in the verbose syntax, and must be a string of predicate(s) that will be appended to the query. Pynonymizer does not check syntax for sql, so you must ensure that what you've written works in your database's language.

Update statements will be grouped on the content of the where key and executed together.

#### Column Strategy: `empty`
Replaces a column with an empty value (usually `''`)

```yaml
column_name: 
  type: empty
  
# Compact Syntax:
column_name: empty
```

#### Column Strategy: `unique_login`
Replaces a column with a unique value that vaguely resembles a username.

```yaml
column_name: 
  type: unique_login

# Compact Syntax:
column_name: unique_login
```

#### Column Strategy: `unique_email`
Replace a column with a unique value that vaguely resembles an email address.
```yaml
column_name: 
  type: unique_email

# Compact Syntax:
column_name: unique_email
```

#### Column Strategy: `literal`
Replace a column with the value specified. 

This will not perform escaping for your language, so you must ensure that it is correct and executable by your provider.
```yaml
column_name: 
  type: literal
  value: RAND()

# Compact Syntax: Not available
```

##### Column Strategy: `fake_update`
Replace a column with a value from a generated data pool (non-unique).

```yaml
column_name: 
  type: fake_update
  fake_type: company_email
  
# Compact Syntax: specify any supported faker method, excluding the keywords `empty`, `unique_login`, `unique_email`
column_name: company_email
```
You can specify a fake update with any one of the following generators:

The values themselves are generated from [Faker](https://faker.readthedocs.io/en/master/)
The aim is to support all of faker's methods, but at the moment, only a small selection are supported.

* first_name
* last_name
* name
* user_name
* email
* company_email
* phone_number
* company
* bs
* catch_phrase
* job
* city
* street_addr
* postcode
* uri
* ipv4_private
* ipv4_public
* file_name
* file_path
* paragraph
* prefix
* random_int
* date_of_birth
* future_date
* past_date
* future_datetime
* past_datetime
* date


## Key: Scripts
Scripts is a top-level key describing SQL statements to be run during the anonymization process. These scripts can also return results that will be entered into the logs.

This might help you to do something specific that pynonymizer may not have a feature for (yet?), or to provider a report on something before you dump/drop/etc.

Scripts are given in the `scripts` top level key. There are two subkeys, `before` and `after`.  In both cases, the required input format
is a list of strings to be run as individual scripts. 

```
scripts:
  after:
    - DELETE FROM students;
    - [...]
  before:
    - DELETE FROM config where name = 'secret';
```

You should recieve the output from each script in the log. The exact format will depend on the database provider. See the script except below:
```
[...]
creating seed table with 3 columns
Inserting seed data
Inserting seed data: 100%|██████████████████| 150/150 [00:05<00:00, 25.98rows/s]
Running before script 0 "SELECT COUNT(1) FROM `accounts`;"
COUNT(1)
1817

Running before script 1 "SELECT SLEEP(1);"
SLEEP(1)
0

Anonymizing 2 tables
Truncating transactions: 100%|████████████████████| 2/2 [00:00<00:00,  2.66it/s]
Running after script 0: "SELECT COUNT(1) FROM `accounts`;"
COUNT(1)
1817
[...]
```

### `before`
Before takes place just before the anonymization starts, after any preparation by the database provider (e.g. seed table, etc)

### `after`
After takes place directly after the anonymization. 