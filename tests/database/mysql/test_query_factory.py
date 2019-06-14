import unittest
from unittest.mock import Mock
import pytest

from pynonymizer.database.exceptions import UnsupportedColumnStrategyError
from pynonymizer.fake import FakeColumn
from pynonymizer.strategy.update_column import ColumnStrategyTypes, FakeUpdateColumnStrategy
import pynonymizer.database.mysql.query_factory as query_factory

"""
These tests are brittle and based on the actual SQL generated. 
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
        self.fake_column1 = Mock(spec=FakeColumn, column_name="test_fake_column_name", sql_type="VARCHAR(50)", get_value=Mock(return_value="test_value1"))
        self.fake_column2 = Mock(spec=FakeColumn, column_name="test_fake_column_name2", sql_type="INT", get_value=Mock(return_value=654))

        self.fake_columns = [self.fake_column1, self.fake_column2]

        self.test_fake_strategy = Mock(spec=FakeUpdateColumnStrategy, strategy_type=ColumnStrategyTypes.FAKE_UPDATE, fake_column=self.fake_column1)
        self.test_fake_strategy2 = Mock(spec=FakeUpdateColumnStrategy, strategy_type=ColumnStrategyTypes.FAKE_UPDATE, fake_column=self.fake_column2)

        self.empty_strategy = Mock(strategy_type=ColumnStrategyTypes.EMPTY)
        self.ulogin_strategy = Mock(strategy_type=ColumnStrategyTypes.UNIQUE_LOGIN)
        self.uemail_strategy = Mock(strategy_type=ColumnStrategyTypes.UNIQUE_EMAIL)

        self.test_column_strategies = {
            "test_column1": self.test_fake_strategy,
            "test_column2": self.test_fake_strategy2,
            "test_column3": self.empty_strategy,
            "test_column4": self.ulogin_strategy,
            "test_column5": self.uemail_strategy
        }

    def test_get_insert_seed_row(self):
        assert "INSERT INTO `seed_table`(`test_fake_column_name`,`test_fake_column_name2`) " \
            "VALUES ('test_value1',654);" == \
             query_factory.get_insert_seed_row("seed_table", self.fake_columns)

    def test_get_create_seed_table(self):
        assert "CREATE TABLE `seed_table` (`test_fake_column_name` VARCHAR(50),`test_fake_column_name2` INT);" == \
            query_factory.get_create_seed_table("seed_table", self.fake_columns)

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
        assert "UPDATE `anon_table` SET " \
            "`test_column1` = ( SELECT `test_fake_column_name` FROM `seed_table` ORDER BY RAND() LIMIT 1)," \
            "`test_column2` = ( SELECT `test_fake_column_name2` FROM `seed_table` ORDER BY RAND() LIMIT 1)," \
            "`test_column3` = ('')," \
            "`test_column4` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())))) )," \
            "`test_column5` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '@', MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '.com') );" == \
            query_factory.get_update_table("seed_table", "anon_table", self.test_column_strategies)
