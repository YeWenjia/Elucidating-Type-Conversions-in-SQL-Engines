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

        config_path = Path(__file__).parent / "newconfig.yml"

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

    #
    def test_null_3(self):
        self.compare_command("SELECT TA.height + TA.height AS col0 FROM TA TA WHERE (1 < NULL AND 1 < 2);")

    def test_isnull_1(self):
        self.compare_command(
            "SELECT 2 AS col0 FROM TB WHERE NULL IS NULL;")

    def test_isnull_2(self):
        self.compare_command(
            "SELECT 2 AS col0 FROM TB WHERE 1 IS NULL AND NULL IS NULL;")


    def test_null_set1(self):
        self.compare_command("SELECT 1 FROM TB INTERSECT SELECT NULL FROM TA;")

    def test_null_set2(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT 1 FROM TB")

    def test_null_set3(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT NULL FROM TA;")

    def test_simplication1(self):
        self.compare_command("SELECT NULL AS col0 FROM TA;")

    def test_simplication2(self):## expression reduction:meeting
        self.compare_command("SELECT fullname FROM TB WHERE EXISTS (SELECT -1 FROM TA);")

    def test_simplication3(self):
        self.compare_command("SELECT 1 FROM TA WHERE 1 IN (SELECT 1 FROM TC);")

    def test_simplication4(self):
        self.compare_command("SELECT 1 AS col0 FROM TB WHERE fullname IN (SELECT NULL AS col0 FROM TA);")

    def test_simplication5(self): ### ignore but written down in paper
        self.compare_command("SELECT 1 FROM TA WHERE EXISTS (SELECT CAST(fullname AS DECIMAL(10,1)) FROM TB);")


    def test_simplication52(self):
        self.compare_command("SELECT CAST(fullname AS DECIMAL(10,1)) FROM TB;")


    def test_simplication53(self):
        self.compare_command("SELECT 1 FROM TA WHERE EXISTS (SELECT 1 FROM TB WHERE CAST(fullname AS DECIMAL(10,1)) = 1);")

    def test_simplication6(self): ### change to string
        self.compare_command("SELECT 1 FROM TC WHERE 1 IN (SELECT '1' FROM TA);")

    def test_simplication8(self): #optimization but written down in paper
        self.compare_command("SELECT CAST(name AS INT) FROM TA WHERE CAST(name AS INT) < NULL;")

    def test_simpli4(self):
        self.compare_command("SELECT name FROM TA WHERE NULL = NULL;")

    def test_tst(self):
        self.compare_command("SELECT NULL AS col0 FROM TA TA0,TB TB1 UNION SELECT TA0.name AS col0 FROM TA TA0,TA TA1 WHERE CAST(TA1.name AS INT) IN (SELECT TB1.realage AS col0 FROM TB TB0,TB TB1 WHERE '9' = TB1.fullheight);")

    def test_tst2(self): # new issue here write this down
        self.compare_command("SELECT 1 AS col0 FROM TA WHERE height IN (SELECT 1 AS col0 FROM TC WHERE 1 < CAST(newname AS DECIMAL(10,1)));")

    def test_tst2a0(self): #
        self.compare_command("SELECT 1 AS col0 FROM TA WHERE height IN (SELECT height AS col0 FROM TC WHERE 1 < CAST(newname AS DECIMAL(10,1)));")

    def test_tst2a1(self):
        self.compare_command("SELECT 1 AS col0 FROM TA WHERE NULL IN (SELECT height AS col0 FROM TC WHERE 1 < CAST(newname AS DECIMAL(10,1)));")


    def test_tst2a(self):
        self.compare_command("SELECT 1 AS col0 FROM TC WHERE 1 < CAST(newname AS DECIMAL(10,1));")

    def test_tst2b(self):
        self.compare_command("SELECT 1 AS col0 FROM TA WHERE height IN (SELECT name AS col0 FROM TC WHERE 1 < CAST(newname AS DECIMAL(10,1)));")


    def test_tst3(self):
        self.compare_command("SELECT CAST(TC0.newname AS INT) AS col0 FROM TC TC0,TB TB1 WHERE EXISTS (SELECT TC1.newname AS col0 FROM TA TA0,TC TC1 WHERE NULL = CAST(TA0.name AS DECIMAL(10,1)));")

    def test_tst4(self):
        self.compare_command("SELECT '10' AS col0 FROM TB TB0,TA TA1 WHERE NULL IN (SELECT NULL AS col0 FROM TC TC WHERE CAST(TC.newname AS DECIMAL(10,1)) < NULL);")

    def test_tst5(self):
        self.compare_command("SELECT '10' AS col0 FROM TA WHERE 1 IN (SELECT NULL AS col0 FROM TC TC WHERE CAST(TC.newname AS INT) < NULL);")

    def test_tst6(self):
        self.compare_command("SELECT '10' AS col0 FROM TA WHERE NULL IN (SELECT NULL AS col0 FROM TC TC WHERE CAST(TC.newname AS INT) < NULL);")

    def test_tst7(self):
        self.compare_command("SELECT '10' AS col0 FROM TA WHERE NULL IN (SELECT 1 AS col0 FROM TC TC WHERE CAST(TC.newname AS INT) < NULL);")

    def test_tst8(self):
        self.compare_command("SELECT '10' AS col0 FROM TA WHERE NULL IN (SELECT newheight AS col0 FROM TC WHERE CAST(newname AS INT) < NULL);")

    def test_new_other1(self):
        self.compare_command("SELECT 1 FROM TB WHERE realage + fullname < NULL + 1;")


    def test_tst9(self):
        self.compare_command("SELECT newheight AS col0 FROM TC WHERE CAST(newname AS INT) < (NULL + 1 IS NULL)")

    def test_tst10(self):
        self.compare_command("SELECT 'mqaak' AS col0 FROM TA WHERE name IN (SELECT realage AS col0 FROM TB WHERE fullheight = 14.4);")

    def test_tst11(self):
        self.compare_command("SELECT 'mqaak' AS col0 FROM TA WHERE name IN (SELECT realage AS col0 FROM TB WHERE false);")

    def test_tst12(self):
        self.compare_command("SELECT 6 AS col0 FROM TB TB UNION SELECT CAST(TC1.newheight AS CHAR) AS col0 FROM TA TA0,TC TC1 WHERE EXISTS (SELECT 'fcxfp' AS col0 FROM TB TB WHERE 'xufbg' < 32.0);")

    def test_tst13(self):
        self.compare_command("SELECT fullheight + height AS col0 FROM TA, TB;")


    def test_tst14(self):
        self.compare_command("SELECT age + name AS col0 FROM TC,TA  WHERE (newage + age IS NULL);")

    def test_tst15(self):
        self.compare_command("SELECT age + name AS col0 FROM TC,TA  WHERE False;")


    def test_mysql_test4(self):
        self.compare_command("SELECT '0' FROM TC UNION SELECT CAST(fullheight AS DECIMAL(10,1)) + CAST(newheight AS DECIMAL(10,1)) AS col0 FROM TB,TC;")

    def test_11_20_am_1(self):
        self.compare_command("SELECT TA.age AS col0 FROM TA TA WHERE (TA.height < NULL OR TA.name + TA.height < 'xdmmf');")

    def test_11_20_am_2(self):
        self.compare_command("SELECT -2 AS col0, TA1.age AS col1 FROM TA TA0,TA TA1 WHERE (CAST(TA0.height AS DECIMAL(10,1)) = TA1.age AND TA1.name = CAST(TA1.name AS TEXT);")

    def test_paper_11_21_am_1(self):
        self.compare_command("SELECT 1 FROM TA WHERE (NULL, 1) IN (SELECT 1, 2 FROM TA);")

    def test_fill_table_1(self):
        self.compare_command(
            "SELECT name + age AS col0 FROM TA WHERE (1 + age IS NULL);")

    def test_fill_table_2(self):
        self.compare_command(
            "SELECT 1 FROM TC WHERE newname IN (SELECT newheight AS col0 FROM TC WHERE FALSE);")

    def test_fill_table_3(self):
        self.compare_command(
            "SELECT 1 FROM TA WHERE EXISTS (SELECT CAST(fullname AS DECIMAL(10,1)) FROM TB);")

    def test_fill_table_4(self):
        self.compare_command("SELECT 1 FROM TB WHERE realage + fullname < NULL + 1")

    def test_fill_table_5(self):
        self.compare_command("SELECT 1 FROM TA WHERE EXISTS (SELECT 1 FROM TB WHERE CAST(fullname AS DECIMAL(10,1)) = 1);")


for i in range(0, 100000):
    simplification = False
    with_null = False

    def gen(index):
        def test_multi(self):
            self.compare_command(generate("Postgres", simplification, with_null), simplification, test_index=index)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestPostgres, test_name, gen(i))


if __name__ == "__main__":
    unittest.main()

"""
# CREATE DATABASE interpreter;
# CREATE USER myuser WITH PASSWORD 'myuser';
# GRANT ALL PRIVILEGES ON DATABASE interpreter TO myuser;
"""
"""
psql -d interpreter -U myuser
myuser
"""

"""
psql -d newinterpreter -U newmyuser
newmyuser
"""