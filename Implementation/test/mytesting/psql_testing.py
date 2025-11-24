import yaml
import psycopg2
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.queryGenerator import *

import unittest

from test.mytesting.engine_testing import TestEngine
from pathlib import Path

# Global counters
test_stats = {
    'total': 0,
    'passed': 0,
    'failed': 0
}

class TestPostgres(TestEngine):

    @classmethod
    def setUpClass(cls):
        cls.engine = Postgres()
        cls.parser = Parser()

        config_path = Path(__file__).parent / "config.yml"

        with open(config_path, "r") as f:
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


for i in range(0, 100000):
    simplification = True
    with_null = False

    def gen(index):
        def test_multi(self):
            self.compare_command(generate("Postgres", simplification, with_null), simplification, test_index=index)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestPostgres, test_name, gen(i))


if __name__ == "__main__":
    unittest.main()
