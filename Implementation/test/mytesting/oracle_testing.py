import yaml
import oracledb
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Oracle import Oracle
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

class TestOracle(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Oracle()
        cls.parser = Parser()

        config_path = Path(__file__).parent / "config.yml"

        with open(config_path, "r") as f:
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
        cls.conn = oracledb.connect(**oracle_conn)

        cls.populateDatabase()

    

for i in range(0, 100000):
    simplification = True
    with_null = False

    def gen(index):

        def test_multi(self):
            self.compare_command(generate("Oracle", simplification, with_null), simplification, test_index=index)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestOracle, test_name, gen(i))
    # globals()[test_multi.__name__] = test_multi

if __name__ == "__main__":
    unittest.main()
    # conn.close()

