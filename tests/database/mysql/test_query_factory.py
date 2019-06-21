import unittest
from unittest.mock import Mock
import pytest
import re
from tests.helpers import ComparableRegex
from pynonymizer.fake import FakeDataType
from pynonymizer.database.exceptions import UnsupportedColumnStrategyError
from pynonymizer.strategy.update_column import (
    UpdateColumnStrategyTypes,
    FakeUpdateColumnStrategy,
    EmptyUpdateColumnStrategy,
    UniqueLoginUpdateColumnStrategy,
    UniqueEmailUpdateColumnStrategy,
    LiteralUpdateColumnStrategy
)
import pynonymizer.database.mysql.query_factory as query_factory

"""
These tests are brittle and based on the actual SQL generatedColumnStrategyTypes. 
The sentiment is to test the 'meaning' of the SQL, rather than the actual formatting, so it may be prudent to replace
these tests with some form of parsing or pattern matching. 

The general idea, however, is that by keeping the queryfactory separate from the provider, it will not change often,
and the sql returned should be very stable.
"""


def test_get_truncate_table():
    assert "SET FOREIGN_KEY_CHECKS=0; " \
           "TRUNCATE TABLE `test`; SET FOREIGN_KEY_CHECKS=1;" == query_factory.get_truncate_table("test")


def test_get_drop_seed_table():
    assert "DROP TABLE IF EXISTS `seed_table`;" == query_factory.get_drop_seed_table("seed_table")


def test_get_create_database():
    assert "CREATE DATABASE `test_database`;" == query_factory.get_create_database("test_database")


def test_get_drop_database():
    assert "DROP DATABASE IF EXISTS `test_database`;" == query_factory.get_drop_database("test_database")


def test_get_dumpsize_estimate():
    assert "SELECT data_bytes FROM " \
           "(SELECT SUM(data_length) AS data_bytes " \
           "FROM information_schema.tables WHERE table_schema = 'test') AS data;" == query_factory.get_dumpsize_estimate("test")


class MysqlQueryFactoryUpdateColumnTests(unittest.TestCase):
    def setUp(self):

        self.str_fake_column_generator = Mock(
            get_data_type=Mock(return_value=FakeDataType.STRING),
            get_value=Mock(return_value="test_value")
        )

        self.int_fake_column_generator = Mock(
            get_data_type=Mock(return_value=FakeDataType.INT),
            get_value=Mock(return_value=645)
        )


        self.fake_strategy1 = FakeUpdateColumnStrategy(self.str_fake_column_generator, "first_name")
        self.fake_strategy2 = FakeUpdateColumnStrategy(self.int_fake_column_generator, "last_name")
        self.empty_strategy = EmptyUpdateColumnStrategy()
        self.ulogin_strategy = UniqueLoginUpdateColumnStrategy()
        self.uemail_strategy = UniqueEmailUpdateColumnStrategy()

        self.literal_strategy = LiteralUpdateColumnStrategy(value="RAND()")

        self.test_column_strategies = {
            "test_column1": self.fake_strategy1,
            "test_column2": self.fake_strategy2,
            "test_column3": self.empty_strategy,
            "test_column4": self.ulogin_strategy,
            "test_column5": self.uemail_strategy,
            "test_column6": self.literal_strategy
        }

    def test_get_insert_seed_row(self):
        insert_seed_row = query_factory.get_insert_seed_row("seed_table", {
                "test_column1": self.fake_strategy1,
                "test_column2": self.fake_strategy2,
            })

        assert insert_seed_row == "INSERT INTO `seed_table`(`first_name`,`last_name`) VALUES ('test_value',645);"

    def test_get_create_seed_table(self):
        assert "CREATE TABLE `seed_table` (`first_name` VARCHAR(4096),`last_name` INT);" == \
            query_factory.get_create_seed_table("seed_table", {
                "test_column1": self.fake_strategy1,
                "test_column2": self.fake_strategy2,
            })

    def test_get_create_seed_table_no_columns(self):
        """
        get_create_seed_table should error when presented with no columns
        """
        with pytest.raises(ValueError) as e_info:
            query_factory.get_create_seed_table("seed_table", [])

    def test_get_update_table_unsupported_column_type(self):
        """
        get_update_table should raise UnsupportedColumnStrategyError if presented with an unsupported column type
        """
        with pytest.raises(UnsupportedColumnStrategyError) as e_info:
            query_factory.get_update_table("seed_table", "anon_table", {
                "test_unsupported_column": Mock(strategy_type="NOT_SUPPORTED")
            })

    def test_get_update_table_fake_column(self):
        update_table_all = query_factory.get_update_table("seed_table", "anon_table", self.test_column_strategies)

        assert [
                "UPDATE `anon_table` SET "
                "`test_column1` = ( SELECT `first_name` FROM `seed_table` ORDER BY RAND() LIMIT 1),"
                "`test_column2` = ( SELECT `last_name` FROM `seed_table` ORDER BY RAND() LIMIT 1),"
                "`test_column3` = (''),"
                "`test_column4` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())))) ),"
                "`test_column5` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '@', MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '.com') ),"
                "`test_column6` = RAND();"
                ] == update_table_all

    def test_get_update_table_fake_column_where(self):
        self.fake_strategy1.where_condition = "cheese = 'gouda'"
        self.ulogin_strategy.where_condition = "marbles > 50"
        result_queries = query_factory.get_update_table("seed_table", "anon_table", self.test_column_strategies)

        # should return 3 grouped queries in list
        where_query1 = "UPDATE `anon_table` SET "\
            "`test_column1` = ( SELECT `first_name` FROM `seed_table` ORDER BY RAND() LIMIT 1) "\
            "WHERE cheese = 'gouda';"

        where_query2 = "UPDATE `anon_table` SET "\
            "`test_column4` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())))) ) "\
            "WHERE marbles > 50;"

        nowhere_query = "UPDATE `anon_table` SET "\
            "`test_column2` = ( SELECT `last_name` FROM `seed_table` ORDER BY RAND() LIMIT 1),"\
            "`test_column3` = (''),"\
            "`test_column5` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '@', MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '.com') )," \
                        "`test_column6` = RAND();"

        print(result_queries)

        assert where_query1 in result_queries
        assert where_query2 in result_queries
        assert nowhere_query in result_queries
        assert len(result_queries) == 3

    def test_get_update_table_literal(self):

        result_queries = query_factory.get_update_table("seed_table", "anon_table", {
            "literal_column": self.literal_strategy
        })

        assert result_queries == [
            "UPDATE `anon_table` SET `literal_column` = RAND();"
        ]