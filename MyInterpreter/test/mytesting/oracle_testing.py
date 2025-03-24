import yaml
import cx_Oracle
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Oracle import Oracle
from interpreter.queryGenerator import *
from test.mytesting.engine_testing import TestEngine

import unittest


class TestOracle(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Oracle()
        cls.parser = Parser()

        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)

        oracle_config = config['oracle']
        dsn = oracle_config['dsn']
        username = oracle_config['user']
        password = oracle_config['password']

        oracle_conn = {
            'user': username,
            'password': password,
            'dsn': dsn
        }
        cls.conn = cx_Oracle.connect(**oracle_conn)

        cls.populateDatabase()

    def test_debug(self):
        self.compare_command(
            "SELECT 0 AS col0 FROM TB WHERE fullheight < fullname;")

    def test_new_bug_1(self):
        self.compare_command("SELECT CAST(height AS INT) AS col0 FROM TA WHERE '4' < 18.3;")

    def test_new_bug_2(self):
        self.compare_command(
            "SELECT CAST(Sub1.col1 AS VARCHAR(255)) AS col0 FROM (SELECT TC.newage + TC.newage AS col1 FROM TC TC) Sub1;")

    def test_new_bug_3(self):
        self.compare_command(
            "SELECT CAST(Sub1.col0 AS INT) AS col0, CAST(Sub1.col0 AS FLOAT) AS col1, CAST(Sub1.col0 AS VARCHAR(255)) AS col2 FROM (SELECT 38.0 AS col0 FROM TB TB) Sub1;")

    def test_new_bug_4(self):
        self.compare_command("SELECT CAST(11.0 AS VARCHAR(255)) AS col0, 11.0 + 11.0 AS col1 FROM TA;")


for i in range(0, 100000):
    def gen():
        simplification = False

        def test_multi(self):
            self.compare_command(generate("Oracle", simplification), simplification)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestOracle, test_name, gen())
    # globals()[test_multi.__name__] = test_multi

if __name__ == "__main__":
    unittest.main()
    # conn.close()
