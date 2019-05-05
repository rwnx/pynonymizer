import unittest
from unittest.mock import Mock
from pynonymizer.strategy.update_column import FakeUpdateColumnStrategy, ColumnStrategyTypes
from pynonymizer.database.mysql import MySqlQueryFactory


class MySqlQueryFactoryTest(unittest.TestCase):
    def test_get_truncate_table(self):
        self.assertEqual(
            "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE `test`; SET FOREIGN_KEY_CHECKS=1;",
            MySqlQueryFactory.get_truncate_table("test")
        )

    def test_get_drop_seed_table(self):
        self.assertEqual(
            "DROP TABLE IF EXISTS `seed_table`;",
            MySqlQueryFactory.get_drop_seed_table("seed_table")

        )

    def test_get_create_database(self):
        self.assertEqual(
            "CREATE DATABASE `test_database`;",
            MySqlQueryFactory.get_create_database("test_database")

        )

    def test_get_drop_database(self):
        self.assertEqual(
            "DROP DATABASE IF EXISTS `test_database`;",
            MySqlQueryFactory.get_drop_database("test_database"),
        )

    def test_get_dumpsize_estimate(self):
        self.assertEqual(
            "SELECT data_bytes FROM (SELECT SUM(data_length) AS data_bytes "
            "FROM information_schema.tables WHERE table_schema = 'test') AS data;",
            MySqlQueryFactory.get_dumpsize_estimate("test")
        )


class FakeColumn:
    def __init__(self, faker_instance, name, sql_type, generator=None):
        self.name = name
        self.sql_type = sql_type
        if generator is None:
            fake_attr = getattr(faker_instance, name)
            self.generator = lambda: fake_attr()
        else:
            self.generator = generator

    def get_value(self):
        return self.generator()

class MysqlQueryFactorySeedTest(unittest.TestCase):
    def setUp(self):
        self.fake_column1 = FakeColumn(Mock, "test_fake_column_name", "VARCHAR(50)", lambda: "test_value1")
        self.fake_column2 = FakeColumn(Mock, "test_fake_column_name2", "INT", lambda: "test_value2")

        self.fake_columns = [self.fake_column1, self.fake_column2]

        self.test_fake_strategy = Mock(strategy_type=ColumnStrategyTypes.FAKE_UPDATE)
        self.test_fake_strategy.fake_column = self.fake_column1
        self.test_fake_strategy2 = Mock(strategy_type=ColumnStrategyTypes.FAKE_UPDATE)
        self.test_fake_strategy2.fake_column = self.fake_column2

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
        self.assertEqual(
            "INSERT INTO `seed_table`(`test_fake_column_name`,`test_fake_column_name2`) "
            "VALUES ('test_value1','test_value2');",
             MySqlQueryFactory.get_insert_seed_row("seed_table", self.fake_columns)
        )

    def test_get_create_seed_table(self):
        self.assertEqual(
            "CREATE TABLE `seed_table` (`test_fake_column_name` VARCHAR(50),`test_fake_column_name2` INT);",
            MySqlQueryFactory.get_create_seed_table("seed_table", self.fake_columns)
        )

    def test_get_update_table_fake_column(self):
        self.assertEqual(
            "UPDATE `anon_table` SET "
            "`test_column1` = ( SELECT `test_fake_column_name` FROM `seed_table` ORDER BY RAND() LIMIT 1),"
            "`test_column2` = ( SELECT `test_fake_column_name2` FROM `seed_table` ORDER BY RAND() LIMIT 1),"
            "`test_column3` = (''),"
            "`test_column4` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())))) ),"
            "`test_column5` = ( SELECT CONCAT(MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '@', MD5(FLOOR((NOW() + RAND()) * (RAND() * RAND() / RAND()) + RAND())), '.com') );",
            MySqlQueryFactory.get_update_table("seed_table", "anon_table", self.test_column_strategies)
        )
