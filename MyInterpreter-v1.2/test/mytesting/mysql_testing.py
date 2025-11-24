# import pymysql
import mysql.connector
import yaml
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mysql import Mysql
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

class TestMysql(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Mysql()
        cls.parser = Parser()

        config_path = Path(__file__).parent / "newconfig.yml"

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        mysql_config = config['mysql']
        host = mysql_config['host']
        database = mysql_config['database']
        username = mysql_config['username']
        password = mysql_config['password']

        mysql_conn = {
            'host': host,
            'database': database,
            'user': username,
            'password': password,
        }

        cls.conn = mysql.connector.connect(**mysql_conn)

        cls.populateDatabase()

    def test_debug(self):
        self.compare_command(
            "SELECT '0' AS col0 FROM TA TA WHERE TA.name < 'hlwen';")

    def test_debug2(self):
        self.compare_command(
            "SELECT CAST(TC1.newname AS DECIMAL(10,1)) + CAST(TC0.newheight AS DECIMAL(10,1)) AS col0 FROM TC TC0,TC TC1 WHERE TC0.newname < 'bzarq';")

    def test_debug3(self):
        self.compare_command(
            "SELECT CAST(TA.height AS CHAR) AS col0 FROM TA TA INTERSECT SELECT TB0.fullname AS col0 FROM TB TB0;"
        )

    def test_null(self):
        self.compare_command("SELECT newage AS col0 FROM TC WHERE (newname = NULL);")

    def test_null_set0(self): # problem int ~> ? write it down and post it
        self.compare_command("SELECT 1 FROM TA INTERSECT SELECT NULL FROM TA;")

    def test_null_set1(self): # ? ~> int
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT 1 FROM TA;")

    def test_null_set2(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT NULL FROM TA")

    def test_null_set3(self): # write it down and post it
        self.compare_command("SELECT 'hi' FROM TA INTERSECT SELECT NULL FROM TA;")

    def test_null_set4(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT 'hi' FROM TA;")

    def test_null_set5(self):
        self.compare_command("SELECT NULL AS col0 FROM TA TA UNION SELECT CAST(TC.newage AS DECIMAL(10,1)) + CAST(TC.newname AS DECIMAL(10,1)) AS col0 FROM TC TC WHERE TC.newage IN (SELECT TB0.fullheight AS col0 FROM TB TB0,TB TB1);")

    def test_null_set5a(self):
        self.compare_command("SELECT NULL AS col0 FROM TA TA")

    def test_null_set5b(self):
        self.compare_command("SELECT 1 FROM TC TC WHERE TC.newage IN (SELECT TB0.fullheight AS col0 FROM TB TB0,TB TB1);")

    def test_null_set6(self):
        self.compare_command("SELECT NULL FROM TA UNION SELECT 1 FROM TA;")

    def test_null_set7(self):
        self.compare_command("SELECT 1 FROM TA UNION SELECT NULL FROM TA;")

    def test_mysql_test1(self):
        self.compare_command("SELECT 6 AS col0 FROM TB TB UNION SELECT CAST(TC1.newheight AS CHAR) AS col0 FROM TA TA0,TC TC1 WHERE EXISTS (SELECT 'fcxfp' AS col0 FROM TB TB WHERE 'xufbg' < 32.0);")

    def test_mysql_test2(self):
        self.compare_command("SELECT -8 AS col0 FROM TC TC WHERE EXISTS (SELECT 'skqoh' AS col0 FROM TC TC0,TC TC1 WHERE NULL < NULL);")

    def test_mysql_test3(self):
        self.compare_command("SELECT -8 AS col0 FROM TC TC WHERE EXISTS (SELECT 'skqoh' AS col0 FROM TC TC0,TC TC1 WHERE NULL < 1);")

    def test_mysql_test4(self): # issue here discuss write it down
        self.compare_command("SELECT '0' FROM TC UNION SELECT CAST(fullheight AS DECIMAL(10,1)) + CAST(newheight AS DECIMAL(10,1)) AS col0 FROM TB,TC;")

    def test_mysql_test4a(self):
        self.compare_command("SELECT '0' FROM TC;")

    def test_mysql_test4b(self):
        self.compare_command("SELECT CAST(fullheight AS DECIMAL(10,1)) + CAST(newheight AS DECIMAL(10,1)) AS col0 FROM TB,TC;")

    def test_mysql_test7(self): ### bug write it down
        self.compare_command("select '0' from TC union select -5.0 + 5.0 from TC;")

    def test_mysql_test7b(self): ### bug write it downs
        self.compare_command("SELECT '1' FROM TA UNION SELECT -5.0 + 6.0 FROM TB;")

    def test_mysql_test7a(self):
        self.compare_command("select '0' from TC union select 0.0 from TC;")

    def test_mysql_test6(self):
        self.compare_command("SELECT CAST(TB0.fullheight AS DECIMAL(10,1)) + CAST(TC1.newheight AS DECIMAL(10,1)) AS col0 FROM TB TB0,TC TC1;")


    def test_mysql_test8(self):
        self.compare_command("SELECT '0' AS col0 FROM TC TC WHERE EXISTS (SELECT NULL AS col0 FROM TB TB0,TC TC1 WHERE CAST(TB0.realage AS DECIMAL(10,1)) < TC1.newage);")


    def test_mysql_test9(self):
        self.compare_command("SELECT TC.newname AS col0, '26.2' AS col1 FROM TC TC EXCEPT SELECT TC0.newname AS col0, CAST(TA1.age AS DECIMAL(10,1)) + CAST(TA1.age AS DECIMAL(10,1)) AS col1 FROM TC TC0,TA TA1;")

    def test_paper_11_18_1(self):
        self.compare_command("SELECT CAST(TA0.name AS DECIMAL(10,1)) + CAST(TA0.name AS DECIMAL(10,1)) AS col0 FROM TA TA0,TC TC1 WHERE (CAST(TC1.newname AS DECIMAL(10,1)) + CAST(TC1.newage AS DECIMAL(10,1)), CAST(TA0.name AS DECIMAL(10,1)) + CAST(TA0.name AS DECIMAL(10,1))) IN (SELECT CAST(Sub1.col0 AS SIGNED) AS col0, Sub1.col0 AS col1 FROM (SELECT CAST(TC.newage AS DECIMAL(10,1)) AS col0 FROM TC TC WHERE TC.newname = TC.newname) Sub1);")

    def test_11_20_am_1(self):
        self.compare_command("SELECT TA.age AS col0 FROM TA TA WHERE (TA.height < NULL OR TA.name + TA.height < 'xdmmf');")


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
    simplification = True
    with_null = False

    def gen(index):
        def test_multi(self):
            self.compare_command(generate("Mysql", simplification, with_null), simplification, test_index= index)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestMysql, test_name, gen(i))

if __name__ == "__main__":
    unittest.main()

"""
mysql -u root -p
password
USE mysqldb;
CREATE DATABASE mysqldb;

"""




"""
SELECT CAST(TA.height AS CHAR) AS col0 FROM TA TA INTERSECT SELECT TB0.fullname AS col0 FROM TB TB0,TA TA1;
"""