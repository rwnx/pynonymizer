# Database Credentials
Pynonymizer requires a connection to a real database in order to perform it's work. 

In most cases (mysql + postgres), pynonymizer uses the databases' CLI tooling to send commands. 
You might have seen something like this:

```
mysql: [Warning] Using a password on the command line interface can be insecure.
```

This occurs because pynonymizer is passing the database password to the CLI using the `-p` option. This means that the password could be visible to other users with access to the running process, e.g. via `ps`.

The same is true for config passed directly to pynonymizer. 

## How do I stop this?
As pynonymizer uses the CLI, the CLI's normal mechanisms for this will also work. 

For providers (mysql and postgres) that allow external configuration, `--db-user` and `--db-pass` will be optional, to support loading credentials through the relevant file:
    * mysql: `my.cnf`/`*.cnf` files: https://dev.mysql.com/doc/refman/8.0/en/option-files.html
    * postgres: `.pgpass` file https://www.postgresql.org/docs/current/libpq-pgpass.html
    * mssql: Not currently supported. 

