from datetime import date, datetime
from pynonymizer.database.exceptions import UnsupportedColumnStrategyError
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes
from pynonymizer.fake import FakeDataType

"""
All Static query generation functions
"""
_FAKE_COLUMN_TYPES = {
    FakeDataType.STRING: "VARCHAR(65535)",
    FakeDataType.DATE: "DATE",
    FakeDataType.DATETIME: "DATETIME",
    FakeDataType.INT: "INT",
}

# Random text function
_RAND_MD5 = "md5(random()::text)"

# Pseudo random integer function
_PSEUDO_RANDOM_INT = "ABS(('x' || MD5(updatetarget::text))::bit(32)::int)"

# Seed Table Id column name
_ID = "_id"


def _get_sql_type(data_type):
    return _FAKE_COLUMN_TYPES[data_type]


def _get_column_subquery(seed_table_name, column_strategy):
    if column_strategy.strategy_type == UpdateColumnStrategyTypes.EMPTY:
        return "('')"
    elif column_strategy.strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL:
        return f"( SELECT CONCAT({_RAND_MD5}, '@', {_RAND_MD5}, '.com') ORDER BY MD5(\"updatetarget\"::text) LIMIT 1)"
    elif column_strategy.strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN:
        return f'( SELECT {_RAND_MD5} ORDER BY MD5("updatetarget"::text) LIMIT 1)'
    elif column_strategy.strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE:
        column = f'"{column_strategy.qualifier}"'
        if column_strategy.sql_type:
            column += "::" + column_strategy.sql_type

        num_rows = f'(SELECT MAX("{_ID}") FROM "{seed_table_name}")'
        pseudo_random_row_id = f"MOD({_PSEUDO_RANDOM_INT}, {num_rows}) + 1"

        return f'( SELECT {column} FROM "{seed_table_name}" WHERE "{_ID}"={pseudo_random_row_id})'
    elif column_strategy.strategy_type == UpdateColumnStrategyTypes.LITERAL:
        return column_strategy.value
    else:
        raise UnsupportedColumnStrategyError(column_strategy)


def _escape_sql_value(value):
    """
    return a sql-ified version of a seed column's value
    Normally this defines the stringification of datatypes and escaping for strings
    """
    if isinstance(value, (str, datetime, date)):
        return "'" + str(value).replace("'", "''") + "'"
    else:
        return str(value)


def _get_qualified_table_name(schema, table):
    return f'"{schema}"."{table}"' if schema else f'"{table}"'


def get_truncate_table(table_strategy):
    return f"TRUNCATE TABLE {_get_qualified_table_name(table_strategy.schema, table_strategy.table_name)} CASCADE;"


# postgres truncates can cascade and are faster than unqualified deletes
# https://www.postgresql.org/docs/9.1/sql-truncate.html
def get_delete_table(table_strategy):
    return f"TRUNCATE TABLE {_get_qualified_table_name(table_strategy.schema, table_strategy.table_name)} CASCADE;"


def get_create_seed_table(table_name, qualifier_map):
    if len(qualifier_map) < 1:
        raise ValueError("Cannot create a seed table with no columns")

    create_columns = [f"{_ID} SERIAL NOT NULL PRIMARY KEY"]
    create_columns += [
        f"{qualifier} {_get_sql_type(strategy.data_type)}"
        for qualifier, strategy in qualifier_map.items()
    ]

    return 'CREATE TABLE "{}" ({});'.format(table_name, ",".join(create_columns))


def get_drop_seed_table(table_name):
    return f"DROP TABLE IF EXISTS {table_name};"


def get_insert_seed_row(table_name, qualifier_map):
    column_names = ",".join([f"{qualifier}" for qualifier in qualifier_map.keys()])
    column_values = ",".join(
        [f"{_escape_sql_value(strategy.value)}" for strategy in qualifier_map.values()]
    )

    return 'INSERT INTO "{}" ({}) VALUES ({});'.format(
        table_name, column_names, column_values
    )


def get_create_database(database_name):
    return f"CREATE DATABASE {database_name};"


def get_drop_database(database_name):
    return [
        # terminate other connections so we can drop
        f"SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{database_name}' AND pid != pg_backend_pid();",
        f"DROP DATABASE IF EXISTS {database_name};",
    ]


def get_update_table(seed_table_name, update_table_strategy):
    # group on where_condition
    # build lists of update statements based on the where
    output_statements = []
    where_update_statements = {}
    for where, column_map in update_table_strategy.group_by_where().items():
        where_update_statements[where] = []
        for column_name, column_strategy in column_map.items():
            where_update_statements[where].append(
                '"{}" = {}'.format(
                    column_name, _get_column_subquery(seed_table_name, column_strategy)
                )
            )

        assignments = ",".join(where_update_statements[where])
        where_clause = f" WHERE {where}" if where else ""

        output_statements.append(
            'UPDATE {} AS "updatetarget" SET {}{};'.format(
                _get_qualified_table_name(
                    update_table_strategy.schema, update_table_strategy.table_name
                ),
                assignments,
                where_clause,
            )
        )

    return output_statements


# TODO: fix for postgres
def get_dumpsize_estimate(database_name):
    return "SELECT 1;"
