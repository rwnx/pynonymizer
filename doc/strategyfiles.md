# Strategyfiles 

Strategyfiles are configurations containing the "What" and the "How" of the anonymization process *for a database*.

They say which tables to access, empty or update to transform the data into an anonymized state.

strategyfiles are written in yaml.

```yaml
tables:
  accounts:
    columns:
      current_sign_in_ip: ipv4_public
      last_sign_in_ip: ipv4_public
      username: user_name
      email: company_email
  transactions: truncate
  other_important_table: truncate
scripts:
  before:
    - DELETE FROM config where name = 'secret';
```

## Tables
Tables is a top-level description of the different tables inside the database that need actions.
It contains a key for each table name.

### Table
Each table has an individual strategy.
* update columns
* truncate

#### Update Columns
value: dict containing `columns` key

Update each column in this table with a column update strategy.
```yaml
tables:
  table_name:
    columns:
      column_name1: empty
      column_name2: unique_login
      column_name3: unique_email
      # fake columns
      column_name4: first_name
      column_name5: last_name
```

##### Available Strategies
* `empty`: Update column with a blank value
* `unique_login`: Update column with a unique string
* `unique_email`: Update column with a unique string which is a valid email
* `fake`: Update column with a non-unique generated value

##### Fake updates
Note that this value will not be unique, as it will be selected from a pool of generated data. This is to improve speed of updates.

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



#### Truncate
value: `"truncate"`

Wipe the entire table using a truncate statement.
```yaml
tables:
  table_name: truncate
```

## Scripts
Scripts can be used to add additional behaviour to the start or the end of an anonymization run. This might help you
to do something specific that pynonymizer may not have a feature for (yet?), or to provider a report on something before you dump/drop/etc.

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