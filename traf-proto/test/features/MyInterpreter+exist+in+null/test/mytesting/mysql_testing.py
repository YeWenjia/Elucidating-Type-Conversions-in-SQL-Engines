# import pymysql
import mysql.connector
import yaml
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mysql import Mysql
from interpreter.queryGenerator import *

from test.mytesting.engine_testing import TestEngine

import unittest


class TestMysql(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Mysql()
        cls.parser = Parser()

        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)

        mysql_config = config['mysql']
        host = mysql_config['host']
        database = mysql_config['database']
        username = mysql_config['username']
        password = mysql_config['password']

        mysql_conn = {
            'host': host,
            'database': database,
            'user': username,
            'password': password,
        }

        cls.conn = mysql.connector.connect(**mysql_conn)

        cls.populateDatabase()

    def test_debug(self):
        self.compare_command(
            "SELECT '0' AS col0 FROM TA TA WHERE TA.name < 'hlwen';")

    def test_debug2(self):
        self.compare_command(
            "SELECT CAST(TC1.newname AS DECIMAL(10,1)) + CAST(TC0.newheight AS DECIMAL(10,1)) AS col0 FROM TC TC0,TC TC1 WHERE TC0.newname < 'bzarq';")


for i in range(0, 100000):
    simplification = False


    def gen():
        def test_multi(self):
            self.compare_command(generate("Mysql", simplification), simplification)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestMysql, test_name, gen())

if __name__ == "__main__":
    unittest.main()
