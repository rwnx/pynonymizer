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