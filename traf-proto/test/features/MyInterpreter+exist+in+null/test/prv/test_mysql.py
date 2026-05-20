# import pymysql
import mysql.connector
import yaml
import sqlparse as mysqlparse
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mysql import Mysql
from interpreter.queryGenerator import *

from test.prv.test_engine import TestEngine

import unittest



class TestMysql(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Mysql()

        with open('config.yml', 'r') as f:
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



    def test_foo(self):
        self.compare_command("SELECT 'ofepx' + 'kexwq' FROM TA;")

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

    # def test_true(self):
    #     self.compare_command("SELECT true FROM TA;")

    def test_number_one(self):
        self.compare_command("SELECT 1 FROM TA;")

    # def test_query_pow_str_int_int(self):
    #     self.compare_command("SELECT POWER('1', 1) FROM TA;")
    #
    # def test_query_pow_str_int_int_union(self):
    #     self.compare_command("SELECT power('1', 1) FROM TA UNION SELECT 2 FROM TA;")
    #
    #
    # # nested problem
    # def test_query_from_subquery(self):
    #     self.compare_command("SELECT power('1', 1) FROM (SELECT 2 FROM TA WHERE 10 = 10) AS sub;")
    #
    # def test_cast_prefix_int(self):
    #     self.compare_command("SELECT POWER('1s1', '1.1s1') FROM TA;")
    #
    # def test_cast_prefix_double(self):
    #     self.compare_command("SELECT POWER('1.1s1', '1s1') FROM TA;")
    #
    # def test_cast_prefix_string(self):
    #     self.compare_command("SELECT POWER('s1.1', '1s1') FROM TA;")
    #
    #
    # def test_cast_prefix_int_sqrt(self):
    #     self.compare_command("SELECT SQRT('1s1') FROM TA;")
    #
    # def test_cast_prefix_double(self):
    #     self.compare_command("SELECT SQRT('1.1s1') FROM TA;")
    #
    # def test_cast_prefix_string(self):
    #     self.compare_command("SELECT SQRT('s1.1') FROM TA;")

    # def test_fail_same_col(self):
    #     self.compare_command("SELECT '6' + 'xikmb' FROM TC AS B0,(SELECT '2' + 'wvssk','rxocy' + 2,C1.name FROM TA AS C1 WHERE NOT ('92.61' = 44.82)) As Sub1 UNION SELECT '77.36' + 82.42 FROM (SELECT B0.name ,'bqvue' + 1,B0.name FROM TA AS B0) As Sub2,A AS C1;")

    # noted!
    # def test_fail_same_col_in_sub(self):
    #     self.compare_command("SELECT 'a','b' FROM (SELECT B0.name,B0.name FROM TA AS B0) AS sub1;")


    def test_generator_example_same_col_diff_order(self):
        self.compare_command("SELECT 'dozxz' FROM TC,TA WHERE 'zxrcu' < '3.5903328854777095';")

    def test_generator_example(self):
        self.compare_command("SELECT newage FROM TB,TC WHERE 'cfffx' = '94.00591374553385';")

    def test_col_not_exists(self):
        self.compare_command("SELECT TA.age FROM (SELECT 1 FROM TA) AS TA, TB;")

    def test_col_not_exists_name(self):
        self.compare_command("SELECT TA.age FROM (SELECT name FROM TA) AS TA, TB;")

    def test_fail_pass(self):
        self.compare_command(
            "SELECT '30.9' + 'zjgoz','4','yycqd' + 'imqfg' FROM (SELECT TA.name FROM TA AS TA WHERE '6' + 23.52 < 'sdzso') As Sub1;")

    def test_intersect_parse(self):
        self.compare_command(
            "SELECT '9' AS col FROM TA AS TB WHERE 8 + 'eiixd' < 33.34 + 69.01 AND '7' < TB.age INTERSECT SELECT '63.58' + 'cnsoa' AS col FROM (SELECT 1 + '8' AS col FROM TA AS TA) As Sub1;")

    def test_union_full(self):
        self.compare_command(
            "SELECT 'ktkky',87.92 + '0','3.57' FROM TA UNION SELECT 10 + '5',9,'ofepx' + 'kexwq' FROM TB;")

    # here
    def test_union_str_int(self):
        self.compare_command("SELECT 'ktkky' FROM TA UNION SELECT 10 + '5' FROM TB;")

    def test_union_type(self):
        self.compare_command("SELECT 'ktkky',87.92 + '0','3.57' FROM TA union select 15,'87.92',3.57 FROM TB;")

    def test_union_same_value(self):
        self.compare_command("SELECT 'ktkky',87.92 + '0','3.57' FROM TA union select 'ktkky','87.92',3.57 FROM TB;")

    def test_lessthan(self):
        self.compare_command("SELECT 1 FROM TC where newname < 'aiqgh';")

    def test_regular(self):
        self.compare_command("SELECT 'c' FROM TC UNION SELECT 0.07 + 10.22 FROM TA;")

    def test_cast(self):
        self.compare_command(
            "SELECT TA.name + TA.name AS col0,CAST(TA.name AS SIGNED) AS col1 FROM TA AS TA WHERE TA.name = CAST(TA.age AS CHAR);")

    def test_cast_simple(self):
        self.compare_command(
            "SELECT CAST(TA.name AS SIGNED) FROM TA AS TA WHERE CAST(TA.name AS CHAR) < TA.name;")

    def test_round(self):
        self.compare_command("SELECT CAST(TA.newheight AS SIGNED) AS col0 FROM TC TA;")

    def test_double(self):
        self.compare_command("SELECT newheight AS col0 FROM TC EXCEPT SELECT CAST(newheight AS CHAR) AS col0 FROM TC;")


    def test_double_int(self):
        self.compare_command("SELECT newage AS col0 FROM TC EXCEPT SELECT CAST(newage AS CHAR) AS col0 FROM TC;")

    def test_double_simple(self):
        self.compare_command("SELECT 1.1 FROM TC EXCEPT SELECT CAST(1.1 AS CHAR) FROM TC;")

    def test_float_double_new(self):
        self.compare_command("SELECT CAST(fullname AS DOUBLE) AS col0 FROM TC,TB  WHERE CAST(newheight AS DOUBLE) = fullheight;")

    def test_point_zero(self):
        self.compare_command("SELECT '6' AS col0 FROM TC EXCEPT SELECT height AS col0 FROM TA;")

    def test_unsigned(self):
        self.compare_command("SELECT 2 AS col0 FROM TB TA WHERE TA.realage < CAST(TA.realage AS SIGNED);")

    def test_no_simplification(self):
        self.compare_command("SELECT 'pkjcs' AS col0, Sub1.col0 + Sub1.col0 AS col1 FROM (SELECT CAST(TB.fullheight AS DECIMAL(10,1)) AS col0 FROM TB TB WHERE TB.realage < TB.fullname + TB.fullname) As Sub1 WHERE ((10 = Sub1.col0 AND Sub1.col0 = Sub1.col0) OR (CAST(Sub1.col0 AS SIGNED) < CAST(Sub1.col0 AS DOUBLE) OR Sub1.col0 = CAST(Sub1.col0 AS SIGNED))) UNION SELECT TA.height AS col0, CAST(TA.age AS DOUBLE) AS col1 FROM TA TA WHERE ((CAST(TA.name AS CHAR) = 2 AND CAST(TA.height AS SIGNED) < TA.age + TA.age) OR TA.name + TA.name < TA.name + TA.height);")

    def test_no_simplification1(self):
        self.compare_command("SELECT 'pkjcs' AS col0, Sub1.col0 + Sub1.col0 AS col1 FROM (SELECT CAST(TB.fullheight AS decimal) AS col0 FROM TB TB WHERE TB.realage < TB.fullname + TB.fullname) As Sub1 WHERE (CAST(Sub1.col0 AS SIGNED) < CAST(Sub1.col0 AS DOUBLE));")


    def test_1(self):
        self.compare_command("select A.c from (select cast(5.9 as decimal) as c FROM TA) AS A where cast(A.c as signed) < cast(A.c as decimal);")


    def test_2(self):
        self.compare_command("select cast(cast(5.9 as decimal) as signed) from TA;")

    def test_3(self):
        self.compare_command("select cast(5.9 as signed) from TA;")

    def test_4(self):
        self.compare_command("select cast(cast(5.9 as decimal) as signed) from TA;")

    def test_5(self):
        self.compare_command("SELECT 'epikz' AS col0, Sub1.col0 + Sub1.col0 AS col1, -8 AS col2 FROM (SELECT CAST(TA.height AS DECIMAL(10,1)) AS col0, CAST(TA.height AS DECIMAL(10,1)) AS col1 FROM TA TA) As Sub1;")

    def test_6(self):
        self.compare_command(" SELECT CAST(Sub1.col0 AS CHAR) AS col2 FROM (SELECT CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA) As Sub1;")

    def test_7(self):
        self.compare_command(" SELECT 1 FROM (SELECT CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA) As Sub1 WHERE CAST(Sub1.col0 AS CHAR) = '6' ;")

    def test_8(self):
        self.compare_command("SELECT CAST(CAST(1 AS DECIMAL(10,1)) AS CHAR) FROM TA;")

    def test_9(self):
        self.compare_command("SELECT CAST(Sub1.col0 AS CHAR) AS col0 FROM (SELECT CAST(TB.fullheight AS DECIMAL(10,1)) AS col0, TB.realage + TB.realage AS col1, TB.fullheight + TB.realage AS col2 FROM TB TB) As Sub1 INTERSECT SELECT CAST(Sub2.col0 AS CHAR) AS col0 FROM (SELECT TC.newheight AS col0, '39.2' AS col1 FROM TC TC) As Sub2;")

    def test_10(self):
        self.compare_command("SELECT CAST(Sub1.col0 AS CHAR) AS col0 FROM (SELECT CAST(TB.fullname AS SIGNED) AS col0 FROM TB TB) AS Sub1 UNION SELECT TB1.fullname + TB1.fullname AS col0 FROM TB TB0,TB TB1;")

    def test_11(self):
        self.compare_command("select cast(cast(1.0 as DECIMAL(10,1)) as CHAR) from TA;")

    def test_12(self):
        self.compare_command("select cast(1.0 as CHAR) from TA;")


    def test_13(self):
        self.compare_command("select cast(1 as DECIMAL(10,1)) from TA;")

    def test_14(self):
        self.compare_command("select height from TA;")

    def test_15(self):
        self.compare_command("SELECT CAST(height+5.5 AS CHAR) FROM TA;")

    def test_16(self):
        self.compare_command("SELECT 1 FROM TA WHERE CAST(height+5.5 AS CHAR) = '0';")

    def test_17(self):
        self.compare_command("SELECT TB1.fullheight + TA0.height AS col0 FROM TA TA0,TB TB1 EXCEPT SELECT Sub1.col1 + Sub1.col1 AS col0 FROM (SELECT TB.fullheight AS col0, TB.fullname AS col1 FROM TB TB) As Sub1 WHERE ((Sub1.col1 + Sub1.col1 = 99.8 AND CAST(Sub1.col1 AS CHAR) = '82.4') AND (Sub1.col1 + Sub1.col0 = Sub1.col1 + Sub1.col1 AND 61.7 = 'rtrcx'));")

    def test_18(self):
        self.compare_command("SELECT 1 FROM TA WHERE CAST(-5.5+5.5 AS CHAR) = '0';")

    def test_19(self):
        self.compare_command("SELECT 87.92 + '0' FROM TA UNION SELECT 9 FROM TB;")

    def test_20(self):
        self.compare_command("SELECT 8 + '0' FROM TA UNION SELECT height+height FROM TA;")

    def test_21(self):
        self.compare_command(
            "SELECT TC0.newage + TB1.fullname AS col0, TB1.fullname + TC0.newname AS col1, TC0.newname AS col2 FROM TC TC0,TB TB1;")

    # def test_22(self):
    #     self.compare_command("SELECT CAST(Sub1.col1 AS SIGNED) AS col0 FROM (SELECT TB.fullheight AS col0, TB.fullname + TB.fullheight AS col1, -9 AS col2 FROM TB TB) As Sub1 WHERE ((10 = Sub1.col2 + Sub1.col0 AND Sub1.col1 + Sub1.col1 < CAST(Sub1.col0 AS SIGNED)) OR (Sub1.col2 + Sub1.col1 < Sub1.col0 + Sub1.col2 AND Sub1.col2 + Sub1.col2 < 30.3));")

    # def test_23(self):
    #     self.compare_command(
    #         "SELECT Sub1.col2 + Sub1.col1 FROM (SELECT 'hi' + 5.1 AS col1, -9 AS col2 FROM TB) As Sub1;")

    ## very important paper
    def test_24(self):
        self.compare_command(
            "SELECT 'hi' + 5.1 + -9 FROM TA;")

    def test_25(self):
        self.compare_command(
            "SELECT 5.1 + -9 FROM TA;")

    def test_26(self):
        self.compare_command(
            "SELECT CAST('hi' AS DECIMAL(10,1)) + 5.1 + -9 FROM TA;")

    def test_27(self):
        self.compare_command(
            "SELECT CAST('hi' + 5.1 + -9 AS CHAR) FROM TA;")

    # def test_in_1(self):
    #     self.compare_command("SELECT 90.0 AS col0, CAST(Sub1.col1 AS DECIMAL(10,1)) + CAST(Sub1.col0 AS DECIMAL(10,1)) AS col1, Sub1.col1 AS col2 "
    #                          "FROM (SELECT TA.age AS col0, TA.name AS col1 FROM TA TA) As Sub1 "
    #                          "UNION SELECT CAST(TC1.newheight AS SIGNED) AS col0, 0 AS col1, CAST(TC1.newage AS DECIMAL(10,1)) AS col2 "
    #                          "FROM TB TB0,TC TC1 WHERE CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) "
    #                          "IN (SELECT Sub2.col0 AS col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.height AS DECIMAL(10,1)) AS col0 "
    #                          "FROM TA TA WHERE CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2 "
    #                          "WHERE CAST(Sub2.col0 AS DECIMAL(10,1)) + CAST(Sub2.col0 AS DECIMAL(10,1)) < '0');")

    def test_in_1_1(self):
        self.compare_command("SELECT 90.0 AS col0, CAST(Sub1.col1 AS DECIMAL(10,1)) + CAST(Sub1.col0 AS DECIMAL(10,1)) AS col1, Sub1.col1 AS col2 "
                             "FROM (SELECT TA.age AS col0, TA.name AS col1 FROM TA TA) As Sub1;")

    def test_in_1_2(self):
        self.compare_command("SELECT CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) AS col0 FROM TB TB0,TC TC1;")

    #
    # def test_in_1_3(self):
    #     self.compare_command("SELECT 1 AS col0 FROM TB TB0,TC TC1 "
    #                          "WHERE CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) "
    #                          "IN "
    #                          "(SELECT Sub2.col0 AS col0 FROM "
    #                          "(SELECT CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA "
    #                          "WHERE CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2 "
    #                          "WHERE CAST(Sub2.col0 AS DECIMAL(10,1)) + CAST(Sub2.col0 AS DECIMAL(10,1)) < '0');")

    # def test_in_1_31(self): # small example
    #     self.compare_command("SELECT 1 AS col0 FROM TB TB0,TC TC1 "
    #                          "WHERE CAST(TC1.newage AS DECIMAL(10,1))"
    #                          "IN "
    #                          "(SELECT Sub2.col0 AS col0 FROM "
    #                          "(SELECT CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA "
    #                          "WHERE CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2);")

    def test_in_1_32(self): # 
        self.compare_command("SELECT CAST(age AS SIGNED) FROM TA, TB WHERE CAST(age AS SIGNED) IN (SELECT S.col0 FROM (SELECT CAST(TA2.height AS SIGNED) AS col0 FROM TA TA2 WHERE 0.0 < TA2.age) AS S);")

    # def test_in_1_33(self): # small example bug?
    #     self.compare_command("SELECT age FROM TB, TA WHERE "
    #                          "CAST(age AS SIGNED) IN (SELECT S.col0 FROM (SELECT CAST(height AS SIGNED) AS col0 FROM TA WHERE 0.0 < age) AS S);")
    #

#    SELECT age FROM TB, TA WHERE CAST(age AS SIGNED) IN (SELECT S.col0 FROM (SELECT CAST(height AS SIGNED) AS col0 FROM TA WHERE 0.0 < TA2.age) AS S);


    def test_in_1_4(self):
        self.compare_command("SELECT CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) FROM TB TB0,TC TC1;")

    def test_in_1_5(self):
        self.compare_command("SELECT Sub2.col0 AS col0 FROM "
                             "(SELECT CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA "
                             "WHERE CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2 "
                             "WHERE CAST(Sub2.col0 AS DECIMAL(10,1)) + CAST(Sub2.col0 AS DECIMAL(10,1)) < '0';")


    # def test_rev_1(self):
    #     self.compare_command("SELECT '0' AS col0 FROM TB TB INTERSECT SELECT CAST(TC0.newage AS DECIMAL(10,1)) + CAST(TA1.age AS DECIMAL(10,1)) AS col0 FROM TC TC0,TA TA1;")

    def test_rev_2(self):
        self.compare_command("SELECT '0' AS col0 FROM TB TB;")

    def test_rev_3(self):
        self.compare_command("SELECT CAST(TC0.newage AS DECIMAL(10,1)) + CAST(TA1.age AS DECIMAL(10,1)) AS col0 FROM TC TC0,TA TA1;")

    # def test_rev_4(self):
    #     self.compare_command("SELECT '0' FROM TB INTERSECT SELECT CAST(1.1 AS DECIMAL(10,1)) + CAST(-1.1 AS DECIMAL(10,1)) FROM TB;")

    def test_rev_7(self):
        self.compare_command("SELECT '0' FROM TB INTERSECT SELECT CAST(0.0 AS DECIMAL(10,1)) + CAST(0.0 AS DECIMAL(10,1)) FROM TB;")

    def test_rev_5(self):
        self.compare_command("SELECT CAST(1.1 AS DECIMAL(10,1)) + CAST(-1.1 AS DECIMAL(10,1)) FROM TB;")

    def test_rev_6(self):
        self.compare_command("SELECT CAST(0.0 AS DECIMAL(10,1)) + CAST(0.0 AS DECIMAL(10,1)) FROM TB;")

# SELECT CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) in (SELECT Sub2.col0 AS col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA WHERE CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2 WHERE CAST(Sub2.col0 AS DECIMAL(10,1)) + CAST(Sub2.col0 AS DECIMAL(10,1)) < '0') FROM TB TB0,TC TC1;

# SELECT 1 AS col0 FROM TB TB0,TC TC1 WHERE CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) IN (SELECT Sub2.col0 AS col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA WHERE CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2 WHERE CAST(Sub2.col0 AS DECIMAL(10,1)) + CAST(Sub2.col0 AS DECIMAL(10,1)) < '0');

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
            self.compare_command(generate("Mysql",simplification), simplification)
        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestMysql, test_name, gen())




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
#
# with open('config.yml', 'r') as f:
#     config = yaml.safe_load(f)

# mysql_config = config['mysql']
# host = mysql_config['host']
# database = mysql_config['database']
# username = mysql_config['username']
# password = mysql_config['password']
#
#
# mysql_conn = {
#     'host': host,
#     'database': database,
#     'user': username,
#     'password': password,
# }


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
# with open("mysql.txt", "r") as file:
#     sql_commands = [q.strip() for q in file.read().splitlines() if q.strip()]
#
# conn = mysql.connector.connect(**mysql_conn)
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
#         print("mysql result:")
#         print(column_names)
#         for row in rows:
#             print(row)
#     except mysql.connector.Error as e:
#         print("Mysql Error:", e)
#         their_error = True
#     parsed = parse_command(command)
#     conn.rollback()
#     print(parsed)
#     try:
#         t = typecheck(dbt, parsed, Mysql())
#         print("pass typechecker!")
#         transd = parsed.trans(dbt, Mysql())
#         print("transd:")
#         print(transd)
#         mytable = transd.run(db, Mysql())
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
#             assert Engine().Compare(mytable.rows, rows, Mysql())
#         else:
#             assert our_error == their_error
#     else:
#         assert our_error == their_error
#
#     cur.close()
#
#
#
#
#
#
# with open("fail_mysql.txt", "r") as file:
#     sql_commands = [q.strip() for q in file.read().split(';')[:-1] if q.strip()]



# SELECT newage FROM B,C WHERE 'cfffx' = '94.00591374553385';

# def test_generator_example_same_table():
#     self.compare_command("SELECT 'dozxz' FROM C,A,C WHERE 'zxrcu' < '3.5903328854777095';")

#
# old_mysql_conn = pytest.fixture(scope='module')(lambda: {
#     'host': host,
#     'database': database,
#     'user': username,
#     'password': password,
# })
#
# for i, command in enumerate(sql_commands):
#     def test_mysql(old_mysql_conn, command = command):
#         conn = pymysql.connect(**old_mysql_conn)
#         # Execute each query one by one
#         cur = conn.cursor()
#         cur.execute(command)
#         rows = cur.fetchall()
#         rows = list(rows)
#         # column_names = [desc[0] for desc in cur.description]
#         mytable = (parse_command(command).trans(dbt, Mysql())).run(db, Mysql())
#         print(command)
#         print(parse_command(command))
#         print("our result:")
#         print(mytable)
#         print("mysql result:")
#         for row in rows:
#             print(row)
#         assert Engine().Compare(mytable.rows, rows, Mysql())
#
#         cur.close()
#         conn.close()
#     test_mysql.__name__ = f"test_mysql_query_{i + 1}"
#     globals()[test_mysql.__name__] = test_mysql






# SELECT B.newage AS cola,5 + 4 AS colb,B.newname AS colc
# FROM TC AS B
# WHERE B.newname < 'aiqgh' OR 3 = 1.89
# EXCEPT
# SELECT C.name AS cola,'yjxvn' + 'ltdtr' AS colb,83.9 + 6 AS colc
# FROM TA AS C
# WHERE NOT (2 + '3' = 65.18);


# (SELECT 'ktkky',87.92 + '0','3.57'
# FROM (SELECT 'xpvtw' + 79.8
# FROM TA AS A
# WHERE NOT (A.age = '9')) As Sub1)
# UNION
# (SELECT 10 + '5',9,'ofepx' + 'kexwq'
# FROM (SELECT 33.84 + 4
# FROM TC AS C
# WHERE NOT ('94.66' + 65.41 < 10)) As Sub2);


# SELECT 14.07 + 7.76 AS cola,A.name AS colb,'oegiy' + 39.52 AS colc
# FROM TA AS A
# WHERE NOT (A.age = '47.92');