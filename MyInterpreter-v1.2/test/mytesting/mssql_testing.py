import yaml
import pyodbc
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mssql import Mssql
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

class TestMssql(TestEngine):

    @classmethod
    def setUpClass(cls):
        cls.engine = Mssql()
        cls.parser = Parser()

        config_path = Path(__file__).parent / "newconfig.yml"

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        mssql_config = config['mssql']
        driver = mssql_config['driver']
        server = mssql_config['server']
        database = mssql_config['database']
        username = mssql_config['username']
        password = mssql_config['password']

        mssql_conn = {
            'Driver': driver,
            'server': server,
            'database': database,
            'user': username,
            'password': password,
        }
        cls.conn = pyodbc.connect(**mssql_conn)

        cls.populateDatabase()

    def test_debug_new_1(self):
        self.compare_command(
            "SELECT 0 AS col0 FROM TB TB WHERE TB.fullheight < TB.fullname;")

    # def test_decimal(self): # we find a bug, here we noted
    #     self.compare_command("select 1.0 + '10.0' from TA;")

    def test_err_1(self):
        self.compare_command("SELECT TC1.newage + TC0.newheight AS col0, TC1.newage + TC0.newheight AS col1 FROM TC TC0,TC TC1;")

    def test_null_set1(self):
        self.compare_command("SELECT 1 FROM TB INTERSECT SELECT NULL FROM TA;")

    def test_null_set2(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT 1 FROM TB")

    def test_null_set3(self):
        self.compare_command("SELECT NULL FROM TA INTERSECT SELECT NULL FROM TA;")

    def test_simpli3(self): # candidate type
        self.compare_command("SELECT name FROM TA WHERE NULL = NULL;")


    def test_simpli2(self):
        self.compare_command("SELECT '-1' FROM TC WHERE -5 = 'dquag';")


    def test_new(self): # no optimization? discuss write it down
        self.compare_command("SELECT 1 FROM TB WHERE realage + fullname < NULL + 1;")

    def test_new2(self): # optimization
        self.compare_command("SELECT 1 FROM TB WHERE realage + fullname < NULL;")

    def test_others1(self): #here
        self.compare_command("SELECT '10' AS col0 FROM TA WHERE name IN (SELECT newheight AS col0 FROM TC WHERE CAST(newname AS INT) < NULL + 1);")

    # def test_others2(self): # they fail # write it down
    #     self.compare_command("SELECT newheight AS col0 FROM TC WHERE CAST(newname AS INT) < NULL + 1;")

    # def test_others3(self): # they dont fail. if newname is name then they succeed, write in the paper # write it down
    #     self.compare_command("SELECT 1 FROM TA WHERE name IN (SELECT name FROM TB WHERE realage + fullname < NULL + 1);")

    def test_paper1(self):
        self.compare_command("SELECT 1 FROM TA WHERE name IN (SELECT 1 FROM TB WHERE realage + fullname < NULL + 1);")


    def test_others4(self): # they fail
        self.compare_command("SELECT '10' AS col0 FROM TA WHERE name IN (SELECT newname AS col0 FROM TC WHERE CAST(newname AS INT) < 1);")


    def test_paper_11_21_am_1(self): # today finding
        self.compare_command("SELECT 1 FROM TA WHERE (NULL, 1) IN (SELECT 1, 2 FROM TA);")

    # def test_paper_11_21_am_2(self): ## different results?
    #     self.compare_command("SELECT 1 FROM TC WHERE 'hlyae' < newname;")

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
            self.compare_command(generate("Mssql", simplification, with_null), simplification, test_index=index)

        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestMssql, test_name, gen(i))

if __name__ == "__main__":
    unittest.main()
    # conn.close()

"""
/opt/homebrew/bin/sqlcmd -S 127.0.0.1,1433 -U SA -P 'ReallyStrongPwd123!' -C
CREATE TABLE TB(realage INT, fullname VARCHAR(255), fullheight DECIMAL(10,1));
GO
"""
"""
mssql -u sa -p reallyStrongPwd123
USE mssqldb
"""

"""
https://builtin.com/software-engineering-perspectives/sql-server-management-studio-mac
docker pull mcr.microsoft.com/mssql/server:2022-latest
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=reallyStrongPwd123" \
   -p 1433:1433 --name sql1 --hostname sql1 \
   -d \
   mcr.microsoft.com/mssql/server:2022-latest

how to connect?
brew install unixodbc
https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver16

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql17 mssql-tools
#CREATE DATABASE mssqldb
"""