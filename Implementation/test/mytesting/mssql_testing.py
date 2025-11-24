import yaml
import pyodbc
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mssql import Mssql
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

class TestMssql(TestEngine):

    @classmethod
    def setUpClass(cls):
        cls.engine = Mssql()
        cls.parser = Parser()

        config_path = Path(__file__).parent / "config.yml"

        with open(config_path, "r") as f:
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



for i in range(0, 100000):
    simplification = True
    with_null = False

    def gen(index):
        def test_multi(self):
            self.compare_command(generate("Mssql", simplification, with_null), simplification, test_index=index)

        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestMssql, test_name, gen(i))

if __name__ == "__main__":
    unittest.main()
    # conn.close()

