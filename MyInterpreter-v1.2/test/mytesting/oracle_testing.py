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

    def test_null(self):
        self.compare_command("SELECT NULL FROM TA;")

    def test_null_set1(self):
        self.compare_command("SELECT 1 FROM TB INTERSECT SELECT NULL FROM TA;")

    def test_null_set2(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT 1 FROM TB")

    def test_null_set3(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT NULL FROM TA;")

    def test_simpli1(self):
        self.compare_command("SELECT height FROM TA UNION SELECT null FROM TC;")

    def test_simpli2(self):
        self.compare_command("SELECT '-1' FROM TC WHERE -5 = 'dquag';")

    def test_simpli3(self):
        self.compare_command("SELECT name FROM TA WHERE NULL = 1;")

    def test_simpli4(self):
        self.compare_command("SELECT name FROM TA WHERE NULL = NULL;")

    def test_simpli5(self): ## PROBLEM, optimization
        self.compare_command("SELECT 1 FROM TB WHERE NULL < realage + fullname;")

    # def test_simpli6(self): ## PROBLEM, optimization
    #     self.compare_command("SELECT 1 FROM TB WHERE realage = 27 and fullheight < realage + fullname;")


    def test_simpli7(self): # discuss, still problem, they fail, put it in the paper
        self.compare_command("SELECT 'mqaak' AS col0 FROM TA WHERE name IN (SELECT realage AS col0 FROM TB WHERE fullheight = 14.4);")

    def test_simpli7a(self): # discuss, still problem, they succeed
        self.compare_command("SELECT 'mqaak' AS col0 FROM TA WHERE name IN (SELECT realage AS col0 FROM TB WHERE false);")

    def test_simpli8(self): # discuss, still problem, they don't fail
        self.compare_command("SELECT TC1.newage + TC1.newheight AS col0 FROM TB TB0,TC TC1 WHERE 25.5 < CAST(TB0.fullheight AS INT) MINUS SELECT CAST(TA1.name AS FLOAT) AS col0 FROM TA TA0,TA TA1 WHERE '-5' < TA1.name + TA1.height;")

    def test_simpli8a(self):
        self.compare_command("SELECT TC1.newage + TC1.newheight AS col0 FROM TB TB0,TC TC1 WHERE 25.5 < CAST(TB0.fullheight AS INT)")

    def test_simpli8b(self):
        self.compare_command("SELECT CAST(TA1.name AS FLOAT) AS col0 FROM TA TA0,TA TA1 WHERE '-5' < TA1.name + TA1.height;")

    def test_simpli8c(self): # they don't fail
        self.compare_command("SELECT 1 FROM TA WHERE FALSE MINUS SELECT CAST(name AS FLOAT) FROM TA;")

    def test_simpli8d(self): # they don't fail
        self.compare_command("SELECT 1 FROM TA WHERE FALSE INTERSECT SELECT CAST(name AS FLOAT) FROM TA;")

    def test_simpli8e(self): # they fail
        self.compare_command("SELECT 1 FROM TA WHERE FALSE UNION SELECT CAST(name AS FLOAT) FROM TA;")

    def test_oracle_test1(self):
        self.compare_command("SELECT fullheight + height AS col0 FROM TA, TB;")

    def test_oracle_test2(self):
        self.compare_command("SELECT TB1.fullheight AS col0 FROM TB TB0,TB TB1 WHERE EXISTS (SELECT CAST(TB.fullheight AS INT) AS col0 FROM TB TB);")

    def test_oracle_test3(self):
        self.compare_command("SELECT NULL AS col0 FROM TB TB UNION SELECT CAST(TB.fullheight AS FLOAT) AS col0 FROM TB TB;")

    def test_oracle_test6(self):
        self.compare_command("SELECT 1 FROM TA WHERE height IN (SELECT name AS col0 FROM TA) INTERSECT SELECT 1 FROM TA WHERE FALSE;")

    def test_oracle_test7(self):# point: the right part is false BUT it fails
        self.compare_command("SELECT 1 FROM TA WHERE CAST(name AS DECIMAL(10,1)) < 1 "
                             "INTERSECT SELECT 1 FROM TA WHERE FALSE;")

    def test_simpli8f(self):  # point: the right part is false but it fails
        self.compare_command("SELECT CAST(name AS FLOAT) FROM TA INTERSECT SELECT 1 FROM TA WHERE FALSE;")

    def test_oracle_test8a(self):
        self.compare_command("SELECT 1 AS col0 FROM TB WHERE ('48.9' IS NULL) INTERSECT SELECT 1 FROM TB  WHERE 40.0 < CAST(fullname AS FLOAT);")

    def test_oracle_test8(self):
        self.compare_command("SELECT '0' AS col0 FROM TB WHERE FALSE INTERSECT SELECT '0'  FROM TB WHERE 40.0 < CAST(fullname AS FLOAT);")

    def test_oracle_test5(self):
        self.compare_command(
            "SELECT 1 FROM TB WHERE EXISTS (SELECT 1 FROM TB WHERE FALSE) INTERSECT SELECT newage FROM TB,TC WHERE realage < CAST(newname AS FLOAT);")

    ############################################################### write it down

    def test_oracle_test5a(self): # point: the left part is empty but they do not optimization
        self.compare_command(
            "SELECT 1 FROM TB WHERE EXISTS (SELECT 1 FROM TB WHERE 8 = fullheight) INTERSECT SELECT newage FROM TB,TC WHERE realage < CAST(newname AS FLOAT);")

    def test_oracle_test5b(self): # point: the left part is empty but they do optimization
        self.compare_command(
            "SELECT 1 FROM TB WHERE EXISTS (SELECT 1 FROM TB WHERE 8 = fullheight) INTERSECT SELECT 2 FROM TB,TC WHERE realage < CAST(newname AS FLOAT);")

    def test_oracle_test5c(self): # point: the left part is empty but they do optimization
        self.compare_command(
            "SELECT 1 FROM TB WHERE EXISTS (SELECT 1 FROM TB WHERE FALSE) INTERSECT SELECT 2 FROM TB,TC WHERE realage < CAST(newname AS FLOAT);")
    ###############################################################



    def test_oracle_test4(self):
        self.compare_command("SELECT age + name AS col0 FROM TA  WHERE (1 + age IS NULL);")

    def test_oracle_paper_11_18_1(self):
        self.compare_command("SELECT age + name AS col0 FROM TA  WHERE (age IS NULL);")

    def test_oracle_paper_11_18_2(self):
        self.compare_command("SELECT 1 AS col0 FROM TA  WHERE (age IS NULL);")

    def test_oracle_paper_11_18_3(self):
        self.compare_command("SELECT age + name AS col0 FROM TA;")

    def test_oracle_paper_11_18_4(self):
        self.compare_command("SELECT age + name AS col0 FROM TA  WHERE (age IS NULL);")

    def test_oracle_test10(self):
        self.compare_command("SELECT age + name AS col0 FROM TA  WHERE (1 + NULL IS NULL);")


    def test_oracle_test10a(self):
        self.compare_command("SELECT age + name AS col0 FROM TA  WHERE (age + NULL IS NULL);")

    def test_oracle_test4a(self):
        self.compare_command("SELECT age + name AS col0 FROM TC,TA WHERE False;")

    ###############################################################


    def test_oracle_test9(self):
        self.compare_command("SELECT 1 + NULL FROM TA;")


    def test_paper_11_17_1(self):
        self.compare_command("SELECT Sub1.col1 FROM (SELECT CAST(newheight AS INT) AS col1 FROM TC WHERE (newname IS NULL)) Sub1;")

    def test_paper_11_17_2(self):
        self.compare_command(
            "SELECT 1 FROM TC WHERE (newname IS NULL);")

    def test_paper_11_17_3(self):
        self.compare_command(
            "SELECT 1 FROM TC WHERE (newheight IS NULL);")

    def test_paper_11_18_pm_1(self):
        self.compare_command("SELECT Sub1.col1 + Sub1.col1 AS col0, Sub1.col1 + Sub1.col0 AS col1, CAST(Sub1.col1 AS INT) AS col2 FROM (SELECT CAST(age AS FLOAT) AS col0, '14.8' AS col1 FROM TA) Sub1 WHERE (Sub1.col0 IS NULL);")

    def test_paper_11_18_pm_2(self):
        self.compare_command("SELECT 'cimev' AS col0, CAST(Sub1.col0 AS INT) AS col1 FROM (SELECT '23.9' AS col0, NULL AS col1 FROM TC) Sub1 WHERE (Sub1.col1 + Sub1.col1 IS NULL);")

    def test_paper_11_19_am_1(self):
        self.compare_command("SELECT TC0.newage AS col0 FROM TC TC0,TA TA1 WHERE CAST(TA1.name AS FLOAT) = CAST(TA1.age AS INT) INTERSECT SELECT -10 AS col0 FROM TC TC0,TA TA1 WHERE (CAST(TC0.newheight AS VARCHAR(255)) IS NULL);")

    def test_paper_11_19_am_2(self):
        self.compare_command("SELECT name + age AS col0 FROM TA WHERE (1 + age IS NULL);")

    def test_paper_11_19_am_3(self):
        self.compare_command("SELECT 1 FROM TC WHERE newname IN (SELECT newheight AS col0 FROM TC WHERE 5 = newheight);")

    def test_paper_11_19_am_4(self):
        self.compare_command("SELECT 1 FROM TC WHERE newname IN (SELECT newheight AS col0 FROM TC WHERE FALSE);")

    def test_fill_table_1(self):
        self.compare_command(
            "SELECT name + age AS col0 FROM TA WHERE (1 + age IS NULL);")

    def test_fill_table_2(self):
        self.compare_command(
            "SELECT 1 FROM TC WHERE newname IN (SELECT newheight AS col0 FROM TC WHERE newheight = 161.0);")

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
            self.compare_command(generate("Oracle", simplification, with_null), simplification, test_index=index)

        return test_multi


    test_name = f"test_multi_query_{i}"
    setattr(TestOracle, test_name, gen(i))
    # globals()[test_multi.__name__] = test_multi

if __name__ == "__main__":
    unittest.main()
    # conn.close()


"""
docker exec -it oracle-db /bin/bash
sqlplus / as sysdba
CONNECT myuser/password
commit;
"""

"""
docker pull gvenzl/oracle-free:latest
docker run -d -p 1521:1521 --name oracle-db -e ORACLE_PASSWORD=password gvenzl/oracle-free:latest
sqlplus / as sysdba
create user myuser identified by password;
ALTER SESSION SET CONTAINER = FREEPDB1;
GRANT CREATE SESSION TO MYUSER;
GRANT CONNECT, RESOURCE TO MYUSER;
GRANT UNLIMITED TABLESPACE TO MYUSER;
COMMIT;
EXIT;
"""