from datetime import date, datetime
from pynonymizer.database.exceptions import UnsupportedColumnStrategyError
from pynonymizer.strategy.update_column import ColumnStrategyTypes
"""
All Static query generation functions
"""


def _get_column_subquery(seed_table_name, column_name, column_strategy):
    # For preservation of unique values across versions of mysql, and this bug:
    # https://bugs.mysql.com/bug.php?id=89474, use md5 based rand subqueries

    if column_strategy.strategy_type == ColumnStrategyTypes.EMPTY:
        return "('')"
    elif column_strategy.strategy_type == ColumnStrategyTypes.UNIQUE_EMAIL:
        return "( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '@', MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '.com') )"
    elif column_strategy.strategy_type == ColumnStrategyTypes.UNIQUE_LOGIN:
        return "( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())))) )"
    elif column_strategy.strategy_type == ColumnStrategyTypes.FAKE_UPDATE:
        return f"( SELECT `{column_strategy.fake_column.column_name}` FROM `{seed_table_name}` ORDER BY RAND() LIMIT 1)"
    else:
        raise UnsupportedColumnStrategyError(column_strategy)


def _escape_sql_value(column):
    """
    return a sql-ified version of a seed column's value
    Normally this defines the stringification of datatypes and escaping for strings
    """
    value = column.get_value()
    if isinstance(value, (str, datetime, date)):
        return "'" + str(value).replace("'", "''") + "'"
    else:
        return str(value)


def get_truncate_table(table_name):
    return f"SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE `{table_name}`; SET FOREIGN_KEY_CHECKS=1;"


def get_create_seed_table(table_name, columns):
    if len(columns) < 1:
        raise ValueError("Cannot create a seed table with no columns")

    column_types = ",".join(map(lambda col: f"`{col.column_name}` {col.sql_type}", columns))
    return f"CREATE TABLE `{table_name}` ({column_types});"


def get_drop_seed_table(table_name):
    return f"DROP TABLE IF EXISTS `{table_name}`;"


def get_insert_seed_row(table_name, columns):
    column_names = ",".join(map(lambda col: f"`{col.column_name}`", columns))
    column_values = ",".join(map(lambda col: _escape_sql_value(col), columns))

    return f"INSERT INTO `{table_name}`({column_names}) VALUES ({column_values});"


def get_create_database(database_name):
    return f"CREATE DATABASE `{database_name}`;"


def get_drop_database(database_name):
    return f"DROP DATABASE IF EXISTS `{database_name}`;"


def get_update_table(seed_table_name, table_name, column_strategies):
    update_statements = []
    for column_name, column_strategy in column_strategies.items():
        update_statements.append(f"`{column_name}` = {_get_column_subquery(seed_table_name, column_name, column_strategy)}")
    update_column_assignments = ",".join( update_statements )

    return f"UPDATE `{table_name}` SET {update_column_assignments};"


def get_dumpsize_estimate(database_name):
    return f"SELECT data_bytes FROM (SELECT SUM(data_length) AS data_bytes FROM information_schema.tables WHERE table_schema = '{database_name}') AS data;"