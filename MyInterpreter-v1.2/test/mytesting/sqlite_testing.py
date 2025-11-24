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

        config_path = Path(__file__).parent / "newconfig.yml"

        with open(config_path, "r") as f:
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

    def test_null_set1(self):
        self.compare_command("SELECT 1 FROM TB INTERSECT SELECT NULL FROM TA;")

    def test_null_set2(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT 1 FROM TB")

    def test_null_set3(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT NULL FROM TA;")

    def test_simplication4(self):
        self.compare_command("SELECT 1 AS col0 FROM TB WHERE fullname IN (SELECT NULL AS col0 FROM TA);")

    def test_simplication5(self):
        self.compare_command("SELECT 1 FROM TA WHERE EXISTS (SELECT CAST(fullname AS DECIMAL(10,1)) FROM TB);")

    def test_simpli4(self): # candidate type
        self.compare_command("SELECT name FROM TA WHERE NULL = NULL;")


    def test_new(self):
        self.compare_command("SELECT 1 FROM TB WHERE NULL < realage + fullname;")

    def test_fix1(self):
        self.compare_command("SELECT '1' + '8' FROM TA;")

    def test_fix2(self):
        self.compare_command("SELECT CAST(Sub1.col0 AS INT) FROM (SELECT '1' AS col0 FROM TC) Sub1;")

    def test_11_20_am_1(self):
        self.compare_command("SELECT TA.age AS col0 FROM TA TA WHERE (TA.height < NULL OR TA.name + TA.height < 'xdmmf');")

    def test_11_20_am_2(self):
        self.compare_command("SELECT 1 FROM TB WHERE (realage = fullheight + fullheight AND 'afidd' < 'pqizx');")

    def test_11_20_am_3(self):
        self.compare_command("SELECT 1 FROM TB WHERE (FALSE AND TRUE);")

    def test_paper_11_21_am_1(self):
        self.compare_command("SELECT 1 FROM TA WHERE (NULL, 1) IN (SELECT 1, 2 FROM TA);")

    def test_fill_table_1(self):
        self.compare_command(
            "SELECT name + age AS col0 FROM TA WHERE (1 + age IS NULL);")

    def test_fill_table_2(self):
        self.compare_command(
            "SELECT 1 FROM TC WHERE newname IN (SELECT newheight AS col0 FROM TC WHERE newheight = 161.0);")

    def test_fill_table_4(self):
        self.compare_command("SELECT 1 FROM TB WHERE realage + fullname < NULL + 1")

    def test_fill_table_5(self):
        self.compare_command("SELECT 1 FROM TA WHERE EXISTS (SELECT 1 FROM TB WHERE CAST(fullname AS DECIMAL(10,1)) = 1);")


for i in range(0, 100000):
    simplification = False
    with_null = False

    def gen(index):
        def test_multi(self):
            self.compare_command(generate("Sqlite", simplification, with_null), simplification, test_index=index)

        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestSqlite, test_name, gen(i))

if __name__ == "__main__":
    unittest.main()

"""
sqlite3 mydatabase;
"""