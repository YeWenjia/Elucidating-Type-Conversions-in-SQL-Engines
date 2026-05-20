import yaml
import pyodbc
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mssql import Mssql
from interpreter.queryGenerator import *
from test.prv.test_engine import TestEngine

import unittest




class TestMssql(TestEngine):

    @classmethod
    def setUpClass(cls):
        cls.engine = Mssql()

        with open('config.yml', 'r') as f:
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
    # def test_cast_int_to_text():
    #     self.compare_command("SELECT CAST(A100.newage AS TEXT) FROM TC AS A100;")
    #
    # def test_cast_int_to_char():
    #     self.compare_command("SELECT CAST(A100.newage AS CHAR) FROM TC AS A100;")

    def test_cast_int_to_varchar(self):
        self.compare_command("SELECT CAST(A100.newage AS VARCHAR(255)) FROM TC AS A100;")

    # text and char
    # cast char to int


    # optimization
    # select 1, age from TA intersect select 2, fullname from B;
    # select 1, age from TA intersect select 1, fullname from B;
    # select 1,2,age from TA intersect select 1,3,fullname from B;
    # union no except yes

    # def test_inter_optimization(self):
    #     self.compare_command("SELECT 7,B.age FROM TA TB INTERSECT SELECT 78.18, A110.fullname FROM TB A110;")
    #
    # def test_inter_optimization2(self):
    #     self.compare_command("SELECT 7,2 FROM TA TB INTERSECT SELECT 78.18, 's' FROM TB A110;")


    def test_char255(self):
        self.compare_command("SELECT C000.newage AS col0,CAST(C1.newage AS VARCHAR(255)) AS col1 FROM TC C000,TC B001,TC C010,TC B011,TC C1 WHERE CAST(C000.newage AS INT) = CAST(C000.newage AS VARCHAR(255));")

    # note! optimization don't generate where for intersect
    # def test_we_fail(self):
    #     self.compare_command("SELECT 5 AS col0 FROM TA WHERE name < CAST(name AS FLOAT) INTERSECT SELECT 10 AS col0 FROM A;")


    def test_test(self):
        self.compare_command("SELECT age AS col0 FROM TA WHERE name < CAST(name AS FLOAT) INTERSECT SELECT age AS col0 FROM TA;")

    # note in the paper if e is v and string type, it needs to check cast
    def test_they_fail(self):
        self.compare_command("SELECT 42.19 AS col0 FROM TA WHERE age + age < age EXCEPT SELECT 'tanog' AS col0 FROM TA WHERE name < '97.96';")


    def test_bug2(self):
        self.compare_command("SELECT 42.19 AS col0 FROM TA WHERE age + age < age EXCEPT SELECT name AS col0 FROM TA WHERE name < '97.96';")


    def test_bug3(self):
        self.compare_command("SELECT CAST('hi' AS INT) FROM TA WHERE age + age < age;")

    def test_bug4(self):
        self.compare_command("SELECT CAST(name AS INT) FROM TA WHERE age + age < age;")

    def test_we_fail2(self):
        self.compare_command("SELECT 2.51 AS col0 FROM TA A WHERE A.name < '71.77';")

    def test_they_fail2(self):
        self.compare_command("SELECT CAST(newage AS FLOAT) AS col0 FROM TC EXCEPT SELECT 'gyeay' AS col0 FROM TB WHERE 'hkxwj' = CAST(fullname AS VARCHAR(255));")


    # note! todo?
    # def test_var_to_float_1(self):
    #     self.compare_command("SELECT '1' AS col0 FROM TC INTERSECT SELECT 0.1 AS col0 FROM TA;")


    def test_var_to_float_2(self):
        self.compare_command("SELECT '1' AS col0 FROM TC INTERSECT SELECT 1.1 AS col0 FROM TA;")

    def test_cast_var_to_float(self):
        self.compare_command("select CAST('5' AS FLOAT) from TA;")


    def test_tabel(self):
        self.compare_command("SELECT name FROM TA;")

    # def test_var_to_float_3(self):
    #     self.compare_command("SELECT CAST(age AS FLOAT) AS col0 FROM TA UNION SELECT A1.newname AS col0 FROM TC A0,C A1 WHERE CAST(A1.newage AS VARCHAR(255)) = A0.newname;")

    # def test_var_to_int (self):
    #     self.compare_command("SELECT C1.age + B0.name AS col0 FROM TA B0,A C1 WHERE C1.name + C1.name = CAST(B0.age AS VARCHAR(255));")

    # # note! only do optimization statically
    # def test_var_to_int2 (self):
    #     self.compare_command("SELECT C1.age + B0.name AS col0 FROM TA B0,A C1 WHERE C1.name + C1.name = CAST(B0.age AS VARCHAR(255));")
    #

    def test_no_simplification(self):
        self.compare_command("SELECT '10' AS col0, Sub1.col1 + Sub1.col0 AS col1, 7 AS col2 FROM (SELECT '1.2' AS col0, 85.9 AS col1 FROM TB TB) As Sub1;")

    def test_no_simplification2(self):
        self.compare_command("SELECT -2 AS col0, CAST(Sub1.col0 AS VARCHAR(255)) AS col1 FROM (SELECT 22.0 AS col0, TB.realage + TB.realage AS col1, TB.fullheight AS col2 FROM TB TB) As Sub1;")

    def test_no_simplification3(self):
        self.compare_command("SELECT -2 AS col0, CAST(Sub1.col0 AS VARCHAR(255)) AS col1 FROM (SELECT 22.0 AS col0, TB.realage + TB.realage AS col1, TB.fullheight AS col2 FROM TB TB) As Sub1;")

    def test_float_to_str(self):
        self.compare_command("select cast(1.0 as VARCHAR(255)) from TA;")

    def test_float_to_str2(self):
        self.compare_command("SELECT CAST(TC.newheight AS VARCHAR(255)) AS col0 FROM TC TC;")

    def test_float_to_str3(self):
        self.compare_command("select cast(cast(1.0 as DECIMAL(10,1)) as VARCHAR(255)) from TA;")

    def test_dont_keep(self):
        self.compare_command("SELECT CAST(Sub1.col0 AS VARCHAR(255)) AS col2 FROM (SELECT TA.height + TA.height AS col0 FROM TA TA) As Sub1;")

    def test_dont_keep2(self):
        self.compare_command("SELECT TA.height + TA.height AS col0 FROM TA TA;")

    def test_no_simplifaction1(self):
        self.compare_command("SELECT Sub1.col1 AS col0, 19.4 AS col1 FROM (SELECT CAST(TB.fullheight AS INT) AS col0, CAST(TB.fullheight AS DECIMAL(10,1)) AS col1, TB.fullheight + TB.fullheight AS col2 FROM TB TB) As Sub1;")

    def test_mssql_1(self):
        self.compare_command("SELECT TC.newage + TC.newheight AS col0, 15.9 AS col1 FROM TC TC;")

    def test_2(self):
        self.compare_command("SELECT -25.9 + 15.9 FROM TA;")


    def test_int_to_decimal_1(self):
        self.compare_command("select cast(1 as decimal(10,1)) from TA;")


    # def test_rev(self):
    #     self.compare_command("SELECT Sub1.col1 AS col0, Sub1.col1 + Sub1.col0 AS col1, Sub1.col1 AS col2 FROM (SELECT 8.9 AS col0, '82.7' AS col1 FROM TA TA) As Sub1;")

    def test_rev_2(self):
        self.compare_command("SELECT '82.7'  + 1 FROM TA;")

    # def test_rev_4(self):
    #     self.compare_command("SELECT Sub1.col1 + 8.9 FROM (SELECT 8.9 AS col0, '82.7' AS col1 FROM TA TA) As Sub1;")

    def test_rev_5(self):
        self.compare_command("select 1.0 + a from (select '82.7' as a from TA) TA;")

    # def test_rev_3(self):
    #     self.compare_command("SELECT '82.7' + 8.9 AS col1 FROM TA;")


    def test_rev_7(self):
        self.compare_command("select 1.0 + '8.7' from TA;")

    # select
    # 100.0
    # union
    # select
    # '82.7';

    def test_rev_7(self):
        self.compare_command("select CAST('82.7' AS DECIMAL(10,1)) from TA;")

    def test_rev_8(self):
        self.compare_command("SELECT TA.age + TA.age AS col0 FROM TA TA MINUS SELECT 17.5 AS col0 FROM (SELECT TB.fullname AS col0 FROM TB TB WHERE (CAST(TB.realage AS INT) = CAST(TB.fullheight AS VARCHAR(255)) OR CAST(TB.realage AS INT) = -1)) Sub1 WHERE CAST(Sub1.col0 AS FLOAT) < Sub1.col0 + Sub1.col0;")

    def test_rev_9(self):
        self.compare_command("SELECT '0' FROM TB INTERSECT SELECT CAST(1.1 AS DECIMAL(10,1)) + CAST(-1.1 AS DECIMAL(10,1)) FROM TB;")

    def test_rev_10_1(self): # a bug about compare decimal
        self.compare_command("select 1.0 + '10.0' from TA;")

    def test_rev_11_1(self):
        self.compare_command("select 1.0 + '1.0' from TA;")



# def clear_txt_file(file_name):
#     with open(file_name, 'r') as file:
#         content = file.read()
#
#     if content:
#         with open(file_name, 'w') as file:
#             file.write('')
#
#
# file_name = 'output.txt'
# clear_txt_file(file_name)

for i in range(0,100000):
    simplification = False
    def gen():
        def test_multi(self):
            self.compare_command(generate("Mssql",simplification), simplification)
        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestMssql, test_name, gen())





if __name__ == "__main__":

    unittest.main()
    # conn.close()





# we have a problem about precision and avoid by generating numbers with the same precision. however, it
# deserves some study and we leave it as a future




















#
#
# db = {
#     "TA": Table(["name", "height", "age"], []),
#     "TB": Table(["realage", "fullname", "fullheight"], []),
#     "TC": Table(["newage", "newheight", "newname"], [])
# }
#
# dbt = {
#     "TA": TableType([NameType("name", SType()),  NameType("height", RType()), NameType("age", ZType())]),
#     "TB": TableType([NameType("realage", ZType()), NameType("fullname", SType()),  NameType("fullheight", RType())]),
#     "TC": TableType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
# }
#
#
#
#
# with open('config.yml', 'r') as f:
#     config = yaml.safe_load(f)
#
# mssql_config = config['mssql']
# driver = mssql_config['driver']
# server = mssql_config['server']
# database = mssql_config['database']
# username = mssql_config['username']
# password = mssql_config['password']
#
#
# mssql_conn = {
#     'Driver': driver,
#     'server': server,
#     'database': database,
#     'user': username,
#     'password': password,
# }
#
#
#
#
# def run(db, query, sql):
#     return query.run(db,sql)
#
# def typecheck(dbt, query, sql):
#     return query.typecheck(dbt,sql)
#
# def trans(dbt, query, sql):
#     return query.trans(dbt, sql)
#
#
# def parse_command(command):
#     parsed = mysqlparse.parse(command)
#     statement = parsed[0]
#     query_object = parse_select(statement)
#     return query_object
#
# with open("fail_mssql.txt", "r") as file:
#     sql_commands = [q.strip() for q in file.read().splitlines() if q.strip()]
#
#
# conn = pyodbc.connect(**mssql_conn)
#
# cur = conn.cursor()
# cur.execute("SELECT * FROM TA;")
# rows = cur.fetchall()
# for r in rows:
#     db["TA"].rows.append(list(r))
#
# print(db)
#
# cur.execute("SELECT * From TB;")
# rows = cur.fetchall()
# for r in rows:
#     db["TB"].rows.append(list(r))
#
# print(db)
#
# cur.execute("SELECT * From TC;")
# rows = cur.fetchall()
# for r in rows:
#     db["TC"].rows.append(list(r))
#
# print(db)
#
#
# def self.compare_command(command: str):
#     rows = []
#     their_error = False
#     our_error = False
#     print(command)
#     try:
#         cur = conn.cursor()
#         cur.execute(command)
#         column_names = [desc[0] for desc in cur.description]
#         rows = cur.fetchall()
#         rows = list(rows)
#         print("mssql result:")
#         print(column_names)
#         for row in rows:
#             print(row)
#     except pyodbc.Error as e:
#         print("Mssql Error:", e)
#         their_error = True
#     conn.rollback()
#     parsed = parse_command(command)
#     print("parsed:")
#     print(parsed)
#     try:
#         t = typecheck(dbt, parsed, Mssql())
#         print("pass typechecker!")
#         transd = parsed.trans(dbt, Mssql())
#         print("transd:")
#         print(transd)
#         mytable = transd.run(db, Mssql())
#         print("our result:")
#         print(mytable)
#     except:
#         our_error = True
#     # print(transd)
#     if not our_error:
#         if not their_error:
#             # print("our result:")
#             # print(mytable)
#             # print("mysql result:")
#             # print(column_names)
#             # for row in rows:
#             #     print(row)
#             print("our_error")
#             print(our_error)
#             print("their_error")
#             print(their_error)
#             assert Engine().Compare(mytable.rows, rows, Mssql())
#         else:
#             assert our_error == their_error
#     else:
#         print("our_error")
#         print(our_error)
#         print("their_error")
#         print(their_error)
#         assert our_error == their_error
#
#     cur.close()
#
#
#
# with open("fail_mssql.txt", "r") as file:
#     sql_commands = [q.strip() for q in file.read().split(';')[:-1] if q.strip()]







# SELECT 0.6 AS col0 FROM TC A0,B B100,C B101,C A11
# UNION SELECT CAST(C1.realage AS VARCHAR(255)) AS col0 FROM TA B0,B C1;
#
# SELECT 57.9 AS col0 FROM TB B UNION SELECT '47.64' AS col0 FROM TB B;
#
# SELECT '60.66' AS col0 FROM TC TB UNION SELECT 78.8 AS col0 FROM TA C;
#
# SELECT 2.99 AS col0 FROM TA A0,B B100,A A101,C B11
# UNION SELECT CAST(B00.realage AS VARCHAR(255)) AS col0 FROM TB B00,A C01,C C1;
#
# SELECT CAST(C.realage AS VARCHAR(255)) AS col0 FROM TB TC EXCEPT SELECT 1.33 AS col0 FROM TA A00,C B01,C C1;
#
# SELECT 9.09 AS col0 FROM TC TA UNION SELECT CAST(B.realage AS VARCHAR(255)) AS col0 FROM TB B;
#
# SELECT CAST(C.newage AS VARCHAR(255)) AS col0 FROM TC C UNION SELECT 1.86 AS col0 FROM TC B;




# for i, command in enumerate(sql_commands):
#     def test_fail(i = i, command = command):
#         print(f"{i+1}")
#         self.compare_command(command)
#
#     test_fail.__name__ = f"test_fail_{i+1}"
#     globals()[test_fail.__name__] = test_fail