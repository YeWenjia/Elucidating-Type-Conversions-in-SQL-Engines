import yaml
import psycopg2
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.queryGenerator import *

import unittest

from test.mytesting.engine_testing import TestEngine


class TestPostgres(TestEngine):

    @classmethod
    def setUpClass(cls):
        cls.engine = Postgres()
        cls.parser = Parser()

        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)

        postgres_config = config['postgres']
        host = postgres_config['host']
        port = postgres_config['port']
        database = postgres_config['database']
        username = postgres_config['username']
        password = postgres_config['password']

        postgresql_conn = {
            'host': host,
            'port': port,
            'dbname': database,
            'user': username,
            'password': password,
        }
        cls.conn = psycopg2.connect(**postgresql_conn)

        cls.populateDatabase()

    def test_debug(self):
        self.compare_command(
            "SELECT CAST(Sub1.col2 AS INT) AS col0 FROM (SELECT '-7' AS col0, 6 AS col1, TC.newheight + TC.newheight AS col2 FROM TC TC) Sub1;")

    def test_debug_1(self):
        self.compare_command("SELECT TB.fullheight AS col0 FROM TB TB WHERE 'foayq' < '44.2';")

    def test_error_1(self):
        self.compare_command(
            "SELECT 'etquo' AS col0, 6 AS col1, CAST(TB.fullheight AS DECIMAL(10,1)) AS col2 FROM TB TB;")

    def test_null_1(self):
        self.compare_command(
            "SELECT 1 + NULL AS col1, 2 AS col0 FROM TB;")

    def test_null_2(self):
        self.compare_command(
            "SELECT 2 AS col0 FROM TB WHERE NULL = NULL;")

    # Problem
    def test_null_3(self):
        self.compare_command("SELECT TA.height + TA.height AS col0 FROM TA TA WHERE (1 < NULL AND 1 < 2);")

    def test_isnull_1(self):
        self.compare_command(
            "SELECT 2 AS col0 FROM TB WHERE NULL IS NULL;")

    def test_isnull_2(self):
        self.compare_command(
            "SELECT 2 AS col0 FROM TB WHERE 1 IS NULL AND NULL IS NULL;")



for i in range(0, 100000):
    simplification = False


    def gen():
        def test_multi(self):
            self.compare_command(generate("Postgres", simplification), simplification)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestPostgres, test_name, gen())

if __name__ == "__main__":
    unittest.main()
