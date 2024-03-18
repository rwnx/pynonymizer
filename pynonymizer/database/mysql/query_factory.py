from datetime import date, datetime
from pynonymizer.database.exceptions import UnsupportedColumnStrategyError
from pynonymizer.strategy.update_column import UpdateColumnStrategyTypes
from pynonymizer.fake import FakeDataType

"""
All Static query generation functions
"""
_FAKE_COLUMN_TYPES = {
    FakeDataType.STRING: "TEXT",
    FakeDataType.DATE: "DATE",
    FakeDataType.DATETIME: "DATETIME",
    FakeDataType.INT: "INT",
}

# For preservation of unique values across versions of mysql, and this bug:
# https://bugs.mysql.com/bug.php?id=89474, use md5 based rand subqueries for unique values (rather than UUIDs)
_RAND_MD5 = "MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND()))"


def _get_sql_type(data_type):
    return _FAKE_COLUMN_TYPES[data_type]


def _get_column_subquery(seed_table_name, column_strategy):
    if column_strategy.strategy_type == UpdateColumnStrategyTypes.EMPTY:
        return "('')"
    elif column_strategy.strategy_type == UpdateColumnStrategyTypes.UNIQUE_EMAIL:
        return f"( SELECT CONCAT({_RAND_MD5}, '@', {_RAND_MD5}, '.com') )"
    elif column_strategy.strategy_type == UpdateColumnStrategyTypes.UNIQUE_LOGIN:
        return f"( SELECT {_RAND_MD5} )"
    elif column_strategy.strategy_type == UpdateColumnStrategyTypes.FAKE_UPDATE:
        column = f"`{column_strategy.qualifier}`"
        if column_strategy.sql_type:
            column = f"CAST({column} AS {column_strategy.sql_type})"
        return f"( SELECT {column} FROM `{seed_table_name}` ORDER BY RAND() LIMIT 1)"
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


def get_truncate_table(table_name):
    return f"SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE `{table_name}`; SET FOREIGN_KEY_CHECKS=1;"


def get_delete_table(table_name):
    return f"DELETE FROM `{table_name}`;"


def get_create_seed_table(table_name, qualifier_map):
    if len(qualifier_map) < 1:
        raise ValueError("Cannot create a seed table with no columns")

    create_columns = [
        f"`{qualifier}` {_get_sql_type(strategy.data_type)}"
        for qualifier, strategy in qualifier_map.items()
    ]

    return "CREATE TABLE `{}` ({});".format(table_name, ",".join(create_columns))


def get_drop_seed_table(table_name):
    return f"DROP TABLE IF EXISTS `{table_name}`;"


def get_insert_seed_row(table_name, qualifier_map):
    column_names = ",".join([f"`{qualifier}`" for qualifier in qualifier_map.keys()])
    column_values = ",".join(
        [f"{_escape_sql_value(strategy.value)}" for strategy in qualifier_map.values()]
    )

    return "INSERT INTO `{}`({}) VALUES ({});".format(
        table_name, column_names, column_values
    )


def get_create_database(database_name):
    return f"CREATE DATABASE `{database_name}`;"


def get_drop_database(database_name):
    return f"DROP DATABASE IF EXISTS `{database_name}`;"


# TODO: this where-grouping behaviour should probably return to the provider, rather than implementing as q-gen logic
def get_update_table(seed_table_name, update_table_strategy):
    # group on where_condition
    # build lists of update statements based on the where
    output_statements = []
    where_update_statements = {}
    for where, column_map in update_table_strategy.group_by_where().items():
        where_update_statements[where] = []
        for column_name, column_strategy in column_map.items():
            where_update_statements[where].append(
                "`{}` = {}".format(
                    column_name, _get_column_subquery(seed_table_name, column_strategy)
                )
            )

        assignments = ",".join(where_update_statements[where])
        where_clause = f" WHERE {where}" if where else ""

        output_statements.append(
            f"UPDATE `{update_table_strategy.table_name}` SET {assignments}{where_clause};"
        )

    return output_statements


def get_dumpsize_estimate(database_name):
    return (
        "SELECT data_bytes "
        "FROM (SELECT SUM(data_length) AS data_bytes FROM information_schema.tables WHERE table_schema = '{}') "
        "AS data;".format(database_name)
    )
