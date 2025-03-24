import yaml
import pyodbc
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mssql import Mssql
from interpreter.queryGenerator import *
from test.mytesting.engine_testing import TestEngine

import unittest


class TestMssql(TestEngine):

    @classmethod
    def setUpClass(cls):
        cls.engine = Mssql()
        cls.parser = Parser()

        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)

        mssql_config = config['mssql']
        driver = mssql_config['driver']
        server = mssql_config['server']
        database = mssql_config['database']
        username = mssql_config['username']
        password = mssql_config['password']

        mssql_conn = {
            'Driver': driver,
            'server': server,
            'database': database,
            'user': username,
            'password': password,
        }
        cls.conn = pyodbc.connect(**mssql_conn)

        cls.populateDatabase()

    def test_debug_new_1(self):
        self.compare_command(
            "SELECT 0 AS col0 FROM TB TB WHERE TB.fullheight < TB.fullname;")


for i in range(0, 100000):
    simplification = False


    def gen():
        def test_multi(self):
            self.compare_command(generate("Mssql", simplification), simplification)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestMssql, test_name, gen())

if __name__ == "__main__":
    unittest.main()
    # conn.close()
