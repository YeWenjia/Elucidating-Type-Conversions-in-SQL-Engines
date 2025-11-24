# import pymysql
import mysql.connector
import yaml
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mysql import Mysql
from interpreter.queryGenerator import *

from test.mytesting.engine_testing import TestEngine

import unittest
from pathlib import Path

# Global counters
test_stats = {
    'total': 0,
    'passed': 0,
    'failed': 0
}

class TestMysql(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Mysql()
        cls.parser = Parser()

        config_path = Path(__file__).parent / "config.yml"

        with open(config_path, "r") as f:
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

for i in range(0, 100000):
    simplification = True
    with_null = False

    def gen(index):
        def test_multi(self):
            self.compare_command(generate("Mysql", simplification, with_null), simplification, test_index= index)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestMysql, test_name, gen(i))

if __name__ == "__main__":
    unittest.main()
