import yaml
import sqlite3
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.queryGenerator import *

import unittest

from test.prv.test_engine import TestEngine


class TestSqlite(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Sqlite()

        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)

        sqlite_config = config['sqlite']
        database = sqlite_config['database']

        sqlite_conn = {
            'database': database,
        }
        cls.conn = sqlite3.connect(**sqlite_conn)

        cls.populateDatabase()

    def test_simple_query(self):
        self.compare_command("SELECT '1' FROM TA UNION SELECT '1' FROM TA;")

    def test_query_union_string_int_float(self):
        self.compare_command("SELECT '1' FROM TA UNION SELECT 1.1 FROM TA;")

    def test_query_union_string_int_int(self):
        self.compare_command("SELECT '1' FROM TA UNION SELECT 1 FROM TA;")

    def test_query_union_int_int(self):
        self.compare_command("SELECT 1 FROM TA UNION SELECT 1 FROM TA;")

    def test_query_union_float_bool(self):
        self.compare_command("SELECT 1.1 FROM TA UNION SELECT true FROM TA;")

    def test_query_union_float_int(self):
        self.compare_command("SELECT 1.1 FROM TA UNION SELECT 2 FROM TA;")

    def test_true(self):
        self.compare_command("SELECT true FROM TA;")

    def test_number_one(self):
        self.compare_command("SELECT 1 FROM TA;")

    def test_generator_example_same_col_diff_order(self):
        self.compare_command("SELECT 'dozxz' FROM TC,TA,TB WHERE 'zxrcu' < '3.5903328854777095';")

    def test_generator_example_same_table(self):
        self.compare_command("SELECT 'dozxz' FROM TC AS TA,TC WHERE 'zxrcu' < '3.5903328854777095';")


    def test_fail(self):
        self.compare_command("SELECT TB.age,'52.37' FROM TA AS TB WHERE '33.03' + 'thzta' = 'svymw' OR 'gtvzc' = 83.76 + 68.5 UNION SELECT 2 + 89.06,'0' + 8 FROM (SELECT '7' + '86.17','cigoq' + 33.02 FROM TA AS TA WHERE 7.45 + 0 < TA.name OR TA.name = 91.39) As Sub1 WHERE 70.41 + 94.97 < 70.34;")

    def test_fail_pass(self):
        self.compare_command("SELECT '30.9' + 'zjgoz','4','yycqd' + 'imqfg' FROM (SELECT TA.name FROM TA AS TA WHERE '6' + 23.52 < 'sdzso') As Sub1;")



    def test_fail_(self):
        self.compare_command("SELECT TB.age,'52.37' FROM TA AS TB "
                        "WHERE '33.03' + 'thzta' = 'svymw' OR 'gtvzc' = 83.76 + 68.5 ")



    def test_fail_cp(self):
        self.compare_command("SELECT 'gkkjf' AS cola FROM TC AS TA WHERE CAST(TA.newage AS text) = TA.newage;")

    def test_fail_cp_add(self):
        self.compare_command("SELECT '2' AS cola FROM TB AS TB WHERE CAST(TB.realage AS text) = TB.realage + TB.fullname")

    def test_address(self):
        self.compare_command("SELECT CAST(TB.fullheight AS FLOAT) AS col0 FROM TB TB WHERE TB.fullname + TB.fullname < TB.fullname;")

    def test_sub_bug(self):
        self.compare_command("SELECT 1 FROM (SELECT '0' AS col1 FROM TA) AS Sub1 WHERE Sub1.col1 < 1;")

    # def test_fail_cp_less(self):
    #     self.compare_command("SELECT 1 AS cola FROM (SELECT '8' AS cola FROM B AS B) As Sub1 WHERE 9 < Sub1.cola")

    def test_bug1(self):
        self.compare_command("select 1 from (select cast(1 as INT) as c FROM TC intersect select cast(1 as INT) FROM TC) A where '0' < A.c;")

    def test_bug2(self):
        self.compare_command("select 1 from (select 1 as c FROM TC intersect select cast(1 as INT) FROM TC) A where '0' < A.c;")

    def test_bug3(self):
        self.compare_command("SELECT TB.newage AS col0 FROM TC TB UNION SELECT TA1.newname + TB0.fullheight AS col0 FROM TB TB0,TC TA1;");

    def test_bug4(self):
        self.compare_command("SELECT CAST(TB1.fullname AS FLOAT) AS col0 FROM TC TC0,TB TB1 UNION SELECT TB.fullname AS col0 FROM TB TB;")

    def test_biconv(self):
        self.compare_command("SELECT TC.newage AS col0 FROM TC TC UNION SELECT '0' AS col0 FROM TC TC;")
    def test_binconv2(self):
        self.compare_command("SELECT A.col0 FROM (SELECT TC.newage AS col0 FROM TC TC UNION SELECT '0' AS col0 FROM TC TC) A WHERE A.col0 < 1;")

    def test_no_simplification_1(self):
        self.compare_command("SELECT CAST(Sub1.col0 AS TEXT) AS col0, Sub1.col0 AS col1, CAST(Sub1.col0 AS TEXT) AS col2 FROM (SELECT CAST(TC.newage AS FLOAT) AS col0 FROM TC TC WHERE (TC.newheight < TC.newname OR (CAST(TC.newage AS INT) < TC.newname + TC.newname OR TC.newname < TC.newname))) As Sub1;")


    def test_no_simplification_22(self):
        self.compare_command(
            "SELECT CAST(Sub1.col1 AS INT) AS col0 FROM (SELECT CAST(TB.fullheight AS TEXT) AS col1, 'upimo' AS col2 FROM TB TB) As Sub1 WHERE (Sub1.col1 + Sub1.col2 = Sub1.col1);")

    def test_no_simplification_23(self):
        self.compare_command(
            "SELECT 1 FROM TB WHERE (CAST(fullheight AS TEXT) + 'upimo' = CAST(fullheight AS TEXT));")


    def test_no_simplification_6(self):
        self.compare_command(
            "SELECT 1 FROM TB WHERE 6 = CAST(fullheight AS TEXT);")

    def test_no_simplification_5(self):
        self.compare_command(
            "SELECT 1 FROM TB WHERE 6.0 = CAST(fullheight AS TEXT);")

    def test_no_simplification_7(self):
        self.compare_command(
            "SELECT CAST(fullheight AS TEXT) + 'upimo' FROM TB;")


    def test_no_simplification_8(self): # str to float '6.0' -> 6.0
        self.compare_command(
            "SELECT CAST(fullheight AS TEXT) FROM TB;")

    def test_no_simplification_9(self):
        self.compare_command(
            "SELECT '6.0' + 'upimo' FROM TB;")

    def test_no_simplification_10(self):  # str to float '6' -> 6.0
        self.compare_command("SELECT '6' + 'upimo' FROM TB;")  # to fix

    def test_no_simplification_11(self):
        self.compare_command("SELECT Sub1.c1 FROM (SELECT CAST(6 AS TEXT) + 'upimo' AS c1 FROM TA) AS Sub1;") # to fix

    def test_nos_1(self):
        self.compare_command("SELECT '52.37' FROM TA WHERE '33.03' + 'thzta' = 'svymw';")

    def test_nos_2(self):
        self.compare_command("SELECT 1 FROM TC WHERE newheight < newname;")

    def test_nos_3(self):
        self.compare_command("SELECT '-4' AS col0 FROM (SELECT '0' AS col0, CAST(TC.newname AS TEXT) AS col1, TC.newname + TC.newage AS col2 FROM TC TC) As Sub1 WHERE (Sub1.col1 + Sub1.col0 = CAST(Sub1.col0 AS TEXT) OR (Sub1.col0 = 'zfxyr' AND CAST(Sub1.col0 AS INT) < Sub1.col2 + Sub1.col0));")

    def test_nos_4(self):
        self.compare_command("SELECT TA.age + TA.height AS col1 FROM TC TC,TA TA WHERE TA.name + TA.height < CAST(TC.newheight AS TEXT);")

    def test_nos_5(self):
        self.compare_command("SELECT CAST(age + height AS TEXT) AS col1 FROM TA;") #here to fix


    def test_nos_6(self):
        self.compare_command("SELECT CAST(1 + 2.0 AS TEXT) AS col1 FROM TA;") #here to fix


    def test_nos_7(self):
        self.compare_command("SELECT CAST(age + age AS TEXT) AS col1 FROM TA;") #here to fix

    def test_nos_8(self):
        self.compare_command("SELECT CAST(height AS TEXT) AS col1 FROM TA;")

    def test_nos_9(self):
        self.compare_command("SELECT CAST(1.0 + 2.0 AS TEXT) AS col1 FROM TA;")

    def test_nos_10(self):  # str to float '6' -> 6.0
        self.compare_command("SELECT '6' + '6.0' FROM TB;") # to fix

    def test_nos_11(self):  # str to float '6' -> 6.0
        self.compare_command("SELECT '6' + '6.0s' FROM TB;") # to fix

    def test_nos_12(self):  # str to float '6' -> 6.0
        self.compare_command("SELECT '6' + c FROM (SELECT CAST('6.0s' AS TEXT) AS c FROM TA);") # to fix

    def test_nos_13(self):  # str to float '6' -> 6.0
        self.compare_command("SELECT '6' + c FROM (SELECT CAST('1s' AS TEXT) AS c FROM TA);") # to fix


    def test_nos_14(self):  # str to float '6' -> 6.0
        self.compare_command("SELECT CAST('1' AS float) FROM TA;")

    def test_nos_15(self):
        self.compare_command("SELECT 'ktkky',87.92 + '0','3.57' FROM TA UNION SELECT 10 + '5',9,'ofepx' + 'kexwq' FROM TB;")

    def test_nos_16(self):
        self.compare_command("SELECT CAST(Sub1.col1 AS DECIMAL(10,1)) AS col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) AS col0, CAST(TA.age AS INT) AS col1 FROM TA TA WHERE (CAST(TA.height AS DECIMAL(10,1)) < CAST(TA.name AS DECIMAL(10,1)) OR TA.name = CAST(TA.height AS INT))) As Sub1 WHERE CAST(Sub1.col1 AS TEXT) = Sub1.col1 + Sub1.col0 UNION SELECT CAST(TB1.fullheight AS TEXT) AS col0 FROM TA TA0,TB TB1 WHERE ((TA0.height < '-3' AND 'bydun' < CAST(TB1.realage AS INT)) AND ('11.4' = TB1.fullheight + TA0.age OR TB1.fullheight < TB1.fullheight + TB1.fullname));")


    def test_nos_17(self):
        self.compare_command(
        "SELECT Sub1.col1 + Sub1.col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) AS col0, CAST(TA.age AS INT) AS col1 FROM TA TA) As Sub1;")



    def test_nos_18(self):
        self.compare_command("SELECT CAST(Sub1.col1 AS DECIMAL(10,1)) AS col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) AS col0, CAST(TA.age AS INT) AS col1 FROM TA TA WHERE (CAST(TA.height AS DECIMAL(10,1)) < CAST(TA.name AS DECIMAL(10,1)) OR TA.name = CAST(TA.height AS INT))) As Sub1 WHERE CAST(Sub1.col1 AS TEXT) = Sub1.col1 + Sub1.col0;")


    ## '6' + 'upimo' = 6
    ## '6.0' + 'upimo' = 6.0
    ## '6' neq to '6.0'
    ## select cast('6' as float); => '6.0'
    ## '6.0' '6'

    def test_nos_19(self):
        self.compare_command("SELECT CAST(1 AS DECIMAL(10,1)) FROM TA;")

    def test_nos_20(self):
        self.compare_command("SELECT CAST(height AS TEXT) FROM TA;")

    def test_nos_21(self):
        self.compare_command("SELECT CAST(6.0 AS TEXT) FROM TA;")

    def test_nos_22(self):
        self.compare_command("SELECT CAST('hi' AS float) AS col0 FROM TA;")

    def test_nos_23(self):
        self.compare_command("SELECT '82.3' AS col0 FROM (SELECT CAST(TC.newname AS DECIMAL(10,1)) AS col0, TC.newname + TC.newage AS col1 FROM TC TC) As Sub1 WHERE (CAST(Sub1.col1 AS TEXT) < Sub1.col0 + Sub1.col1 AND Sub1.col1 = Sub1.col1);")

    def test_nos_24(self):
        self.compare_command("SELECT 'xqnjs' AS col0, 5.3 AS col1, Sub1.col2 + Sub1.col1 AS col2 FROM (SELECT TB.realage AS col0, TB.fullname AS col1, CAST(TB.fullname AS DECIMAL(10,1)) AS col2 FROM TB TB) As Sub1 WHERE (Sub1.col0 + Sub1.col0 < -3 OR (Sub1.col2 + Sub1.col2 < Sub1.col0 + Sub1.col1 AND Sub1.col2 + Sub1.col0 = CAST(Sub1.col0 AS TEXT)));")

    def test_rev_1(self):
        self.compare_command("SELECT '0' FROM TB INTERSECT SELECT CAST(1.1 AS DECIMAL(10,1)) + CAST(-1.1 AS DECIMAL(10,1)) FROM TB;")

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
            self.compare_command(generate("Sqlite", simplification),simplification)
        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestSqlite, test_name, gen())



if __name__ == "__main__":

    unittest.main()


































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
# with open('config.yml') as f:
#     config = yaml.safe_load(f)
#
# sqlite_config =  config['sqlite']
# database = sqlite_config['database']
#
#
# sqlite_conn = {
#     'database': database,
# }
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
#     parsed = sqlparse.parse(command)
#     statement = parsed[0]
#     query_object = parse_select(statement)
#     return query_object
#
#
# conn = sqlite3.connect(**sqlite_conn)
#
# cur = conn.cursor()
# cur.execute("SELECT * From TA;")
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
# def compare_command(command: str):
#     rows = []
#     their_error = False
#     our_error = False
#     print(command)
#     try:
#         cur = conn.cursor()
#         cur.execute(command)
#         column_names = [desc[0] for desc in cur.description]
#         rows = cur.fetchall()
#         print("sqlite result:")
#         print(column_names)
#         for row in rows:
#             print(row)
#     except sqlite3.Error as e:
#         print("Sqlite Error:", e)
#         their_error = True
#     parsed = parse_command(command)
#     conn.rollback()
#     print("parsed:")
#     print(parsed)
#     try:
#         t = typecheck(dbt, parsed, Sqlite())
#         ("pass typechecker!")
#         transd = parsed.trans(dbt, Sqlite())
#         print("transd:")
#         print(transd)
#         mytable = transd.run(db, Sqlite())
#         print("our result:")
#         print(mytable)
#     except:
#         our_error = True
#     if not our_error:
#         if not their_error:
#             assert Engine().Compare(mytable.rows, rows, Sqlite())
#         else:
#             print("our_error")
#             print(our_error)
#             print("their_error")
#             print(their_error)
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
# with open("fail_sqlite.txt", "r") as file:
#     sql_commands = [q.strip() for q in file.read().split(';')[:-1] if q.strip()]


# def test_fail_where_name():
#     compare_command("SELECT 4 + 43.18 FROM "
#                     "(SELECT C.realage,2,'39.14' FROM B AS C) As Sub1 "
#                     "UNION SELECT 18.05 + 1.04 FROM C AS C WHERE NOT ('10' < C.newage);")

# def test_fail_where_name():
#     compare_command("SELECT 4 + 43.18 FROM (SELECT C.realage,2,'39.14' FROM B AS C) As Sub1 UNION SELECT 18.05 + 1.04 FROM C AS C WHERE NOT ('10' < C.newage);")
#

# for i, command in enumerate(sql_commands):
#     def test_fail(command = command, i = i):
#         print(f"{i+1}")
#         # print(command)
#         compare_command(command)
#
#     test_fail.__name__ = f"test_fail_{i+1}"
#     globals()[test_fail.__name__] = test_fail




# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,Sub1.col01 AS cola
# FROM (SELECT B.name AS col00,B.age AS col01,'37.04' AS cola
# FROM TA AS B) As Sub1
# WHERE Sub1.cola < Sub1.cola + Sub1.col01;

# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,Sub1.col01 AS cola
# FROM (SELECT B.fullname AS col00,B.realage AS col01,'8' AS cola
# FROM B AS B) As Sub1
# WHERE 9 < Sub1.cola;

# def test_query_pow_str_int_int():
#     compare_command("SELECT POWER('1', 1) FROM TA;")
#
# def test_query_pow_str_int_int_union():
#     compare_command("SELECT power('1', 1) FROM TA UNION SELECT 2 FROM TA;")
#
# def test_cast_prefix_int():
#     compare_command("SELECT POWER('1s1', '1.1s1') FROM TA;")
#
# def test_cast_prefix_double():
#     compare_command("SELECT POWER('1.1s1', '1s1') FROM TA;")
#
# def test_cast_prefix_string():
#     compare_command("SELECT POWER('s1.1', '1s1') FROM TA;")
#
#
# def test_cast_prefix_int_sqrt():
#     compare_command("SELECT SQRT('1s1') FROM TA;")
#
# def test_cast_prefix_double_sqrt():
#     compare_command("SELECT SQRT('1.1s1') FROM TA;")
#
# def test_cast_prefix_string_sqrt():
#     compare_command("SELECT SQRT('s1.1') FROM TA;")
#
# def test_cast_sqrt_str_int():
#     compare_command("SELECT SQRT('1') FROM TA;")
#
# def test_cast_sqrt_str_double():
#     compare_command("SELECT SQRT('1.1') FROM TA;")


# SELECT 4 + 43.18
# FROM (SELECT C.realage,2,'39.14'
# FROM B AS C) As Sub1
# UNION
# SELECT 18.05 + 1.04
# FROM C AS C
# WHERE NOT ('10' < C.newage);


# SELECT 'sedhx' + 23.31
# FROM C AS B0,(SELECT '75.71' + 'ncoiq'
# FROM C AS A1
# WHERE NOT ('8' < A1.newage)) As Sub1
# EXCEPT
# SELECT '44.06'
# FROM TA AS C
# WHERE C.name < 'fckjh' + 45.17 OR C.age = 16.61 + 50.11;


# SELECT '44.87',A01.age,'1'
# FROM (SELECT 15.72 + 'sumde','nhuaw',A00.newname
# FROM C AS A00) As Sub1,A AS A01,C AS A1
# WHERE NOT (10 + 1 < 99.19);


# SELECT '7',10 + 'plvjt','79.72'
# FROM (SELECT 'gbqxi'
# FROM B AS B
# WHERE NOT (B.fullname < 'bekec')) As Sub1
# EXCEPT
# SELECT 72.0,4 + 53.29,40.64 + 9
# FROM (SELECT C00.realage
# FROM B AS C00
# WHERE 'iiwxf' = C00.realage AND 1 = 62.33 + 'stxim') As Sub2,B AS B01,(SELECT 13.71 + 63.62,7,A1.age
# FROM TA AS A1) As Sub3;

# SELECT C.fullname,'19.99' + 'qwwvp','0'
# FROM B AS C
# WHERE NOT (7 < C.realage);


# SELECT 44.11
# FROM (SELECT B.age
# FROM TA AS B) As Sub1
# WHERE NOT ('rbeoy' + 6 < 63.14 + '13.05');



# SELECT '6' + 'xikmb'
# FROM C AS B0,(SELECT '2' + 'wvssk','rxocy' + 2,C1.name
# FROM TA AS C1
# WHERE NOT ('92.61' = 44.82)) As Sub1
# UNION
# SELECT '77.36' + 82.42
# FROM (SELECT B0.name,'bqvue' + 1,B0.name
# FROM TA AS B0) As Sub2,A AS C1;


# SELECT 'mmmsi' + '9'
# FROM TA AS B
# WHERE NOT (B.age < B.age)
# EXCEPT
# SELECT 73.12 + '0'
# FROM B AS TC;