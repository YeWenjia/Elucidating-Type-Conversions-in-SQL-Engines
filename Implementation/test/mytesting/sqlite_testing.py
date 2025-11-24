import yaml
import sqlite3
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Sqlite import Sqlite
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

class TestSqlite(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Sqlite()
        cls.parser = Parser(use_decimal=False)

        config_path = Path(__file__).parent / "config.yml"

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        sqlite_config = config['sqlite']
        database = sqlite_config['database']

        sqlite_conn = {
            'database': database,
        }
        cls.conn = sqlite3.connect(**sqlite_conn)

        cls.populateDatabase(use_decimal=False)


for i in range(0, 100000):
    simplification = True
    with_null = False

    def gen(index):
        def test_multi(self):
            self.compare_command(generate("Sqlite", simplification, with_null), simplification, test_index=index)

        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestSqlite, test_name, gen(i))

if __name__ == "__main__":
    unittest.main()

