import yaml
import sqlite3
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.queryGenerator import *

import unittest

from test.mytesting.engine_testing import TestEngine


class TestSqlite(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Sqlite()
        cls.parser = Parser(use_decimal=False)

        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)

        sqlite_config = config['sqlite']
        database = sqlite_config['database']

        sqlite_conn = {
            'database': database,
        }
        cls.conn = sqlite3.connect(**sqlite_conn)

        cls.populateDatabase(use_decimal=False)

    def test_debug(self):
        self.compare_command("SELECT 0 AS col0 FROM TB TB WHERE TB.fullheight < TB.fullname;")

    def test_bug_new_1(self):
        self.compare_command(
            "SELECT TA1.name AS col0 FROM TB TB0,TA TA1 UNION SELECT fullheight + height AS col0 FROM TA,TB;")

    def test_bug_new_2(self):
        self.compare_command("SELECT fullheight + height AS col0 FROM TA,TB;")

    def test_bug_new_3(self):
        self.compare_command("SELECT 5.1 + 5.8 AS col0 FROM TA;")

    def test_bug_4(self):
        self.compare_command("SELECT 5.1 + 5.8 FROM TA union select 10.9 FROM TA;")

    def test_bug_5(self):
        self.compare_command(
            "SELECT TB.fullheight, TB.fullname, TB.fullheight + TB.fullname FROM TB TB WHERE TB.fullheight + TB.fullname < TB.fullheight")

    def test_bug_6(self):
        self.compare_command(
            "SELECT '9' AS col0 FROM (SELECT TC.newheight + TC.newheight AS col0 FROM TC TC) Sub1 WHERE CAST(Sub1.col0 AS TEXT) = CAST(Sub1.col0 AS DECIMAL(10,1));")

    def test_bug_7(self):
        self.compare_command(
            "SELECT TA.age + TA.height AS col0 FROM TA TA EXCEPT SELECT TC.newheight + TC.newage AS col0 FROM TC TC;")


for i in range(0, 100000):
    simplification = False


    def gen():
        def test_multi(self):
            self.compare_command(generate("Sqlite", simplification), simplification)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestSqlite, test_name, gen())

if __name__ == "__main__":
    unittest.main()
