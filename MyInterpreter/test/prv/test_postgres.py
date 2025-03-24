import yaml
import psycopg2
import pytest
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.queryGenerator import *

import unittest

from test.prv.test_engine import TestEngine

# db = {
#     "A": Table(["name", "age"], [["Alice", 25], ["Bob", 30]]),
#     "B": Table(["fullname", "realage"], [["Bob", 30], ["Alice", 25]]),
#     "C": Table(["newage", "newname"], [[30, "Bob"], [25,"Alice"]])
# }
#
# dbt = {
#     "A": TableType([NameType("name", SType()), NameType("age", ZType())]),
#     "B": TableType([NameType("fullname", SType()), NameType("realage", ZType())]),
#     "C": TableType([NameType("newage", ZType()), NameType("newname", SType())])
# }








# def simpl_parse(sql_command):
#     if sql_command == 'SELECT name,age FROM A;':
#         return Proj(Beta([Alias(Name("name"), "name"), Alias(Name("age"), "age")]), Rel("A", ["name", "age"]))
#     elif sql_command == 'SELECT name FROM A;':
#         return Proj(Beta([Alias(Name("name"), "name")]), Rel("A", ["name", "age"]))
#     else:
#         print("queries not found!")


# # Split the queries into individual statements and remove the empty
# with open("sql.txt", "r") as file:
#     sql_commands = [q.strip() for q in file.read().splitlines() if q.strip()]
#
#     # sql_commands = file.read().split(';')[:-1]













class TestPostgres(TestEngine):


    @classmethod
    def setUpClass(cls):
        cls.engine = Postgres()


        with open('config.yml', 'r') as f:
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

    def test_fail_colnum_union(self):
        self.compare_command("(SELECT '86.74299345112773',TB.newname,TB.newname FROM TC AS TB) "
                        "UNION"
                        " (SELECT TA.name FROM TA AS TA);")

    def test_col_not_exists(self):
        self.compare_command("SELECT TA.age FROM (SELECT 1 FROM TA) AS TA, TB;")

    def test_col_not_exists_name(self):
        self.compare_command("SELECT TA.age FROM (SELECT name FROM TA) AS TA, TB;")


    # def test_fail_same_col_name(self):
    #     self.compare_command("SELECT SQRT('2') "
    #                     "FROM "
    #                     "(SELECT fullname,fullname "
    #                     "FROM TB  WHERE NOT (realage = realage)) As Sub2;")

    # def test_fail_float_close(self):
    #     self.compare_command("(SELECT SQRT(2) FROM TC AS C0, "
    #                     "(SELECT C1.realage FROM B AS C1) As Sub1) "
    #                     "UNION"
    #                     " (SELECT SQRT(93.4) FROM TA AS B);")


    #def test_fail_pass(self):
    #    self.compare_command("SELECT '30.9' + 1.1 FROM (SELECT A.name FROM TA AS TA WHERE 6 < 1) As Sub1;")



    # shortcut or not?
    # def test_fail_cast_and_name(self):
    #     self.compare_command("SELECT 3 AS col FROM B WHERE 5 = CAST(fullname AS float) AND fullname < '42.29'")


    def test_fail_cast_and(self):
        self.compare_command("SELECT 3 AS col FROM TB WHERE 5 = CAST('hello' AS float) AND fullname < '42.29'")

    # sub lazy?
    def test_fail_sub_cast(self):
        self.compare_command("SELECT Sub1.col00 FROM (SELECT CAST(name AS float) as col00 FROM TA) As Sub1; ")

    def test_fail_union(self):
        self.compare_command("(SELECT TC.name FROM TA AS TC "
                        "WHERE TC.name < TC.name OR TC.age = SQRT('97.61')) "
                        "UNION "
                        "(SELECT TA.newage "
                        "FROM TC AS TA WHERE SQRT(61.85) = SQRT(9));")

    def test_fail_eq(self):
        self.compare_command("SELECT 1 FROM (SELECT 2 FROM TA WHERE 1.1 = '3') As Sub1,TC WHERE 1 = newname;")

    def test_fail_eq(self):
        self.compare_command("SELECT 1 FROM (SELECT 2 FROM TA WHERE 1 = 2) As Sub1,"
                        "TC WHERE 1 = newname;")


    def test_fail_debugg(self):
        self.compare_command("SELECT TA1.age AS col0,TA1.age + TA1.age AS col1 FROM TC C0,TA TA1;")


    def test_fail_debug2(self):
        self.compare_command("SELECT TC.newage AS col0 FROM TC TC WHERE CAST(TC.newage AS FLOAT) = 49.11;")

    def test_bug(self):
        self.compare_command("SELECT 42.19 AS col0 FROM TA WHERE age + age < age EXCEPT SELECT 'tanog' AS col0 FROM TA WHERE name < '97.96';")

    def test_bug2(self):
        self.compare_command("SELECT 42.19 AS col0 FROM TA WHERE age + age < age EXCEPT SELECT name AS col0 FROM TA WHERE name < '97.96';")


    def test_bug3(self):
        self.compare_command("SELECT CAST('hi' AS INT) FROM TA WHERE age + age < age;")

    def test_bug4(self):
        self.compare_command("SELECT CAST(name AS INT) FROM TA WHERE 2 < 1;")

    def test_bug5(self):
        self.compare_command("SELECT CAST('hi' AS INT) FROM TA;")

    def test_fail_bigtable(self):
       self.compare_command("SELECT CAST(TB.newheight AS TEXT) AS col0 FROM TC TB WHERE TB.newheight = CAST(TB.newheight AS FLOAT);")

    def test_neg(self):
        self.compare_command("SELECT '-1' + 1 FROM TA;")

    def test_neg_float(self):
        self.compare_command("SELECT '-1.1' + 1.1 FROM TA;")

    def test_run(self):
        self.compare_command("SELECT CAST(TC.age AS TEXT) AS col0 FROM TA TC WHERE '27.42' < '-5'; ")

    def test_opti1(self):
        self.compare_command("SELECT 34.4 AS col0, CAST('es' AS FLOAT) AS col1 FROM TC  As Sub1 WHERE False;")
    def test_opti2(self):
        self.compare_command("SELECT Sub1.col1 AS col0, CAST(Sub1.col1 AS FLOAT) AS col1 FROM (SELECT 34.04 AS col0, 'eksnf' AS col1 FROM TC TA) As Sub1 WHERE '1' = CAST(Sub1.col0 AS TEXT);", False)
    def test_opti3(self):
        self.compare_command("SELECT Sub1.col1 AS col0, CAST('eksnf' AS FLOAT) AS col1 FROM (SELECT 34.04 AS col0, 'eksnf' AS col1 FROM TC TA) As Sub1 WHERE '1' = CAST(Sub1.col0 AS TEXT);")

    #round
    def test_impl_ascr(self):
        self.compare_command("SELECT CAST(TB.fullheight AS INT) AS col0 FROM TB TB UNION SELECT -6 AS col0 FROM TB TB;")

    def test_impl_ascr2(self):
        self.compare_command("SELECT '4' AS col0 FROM TB TB UNION SELECT TA.age + TA.age AS col0 FROM TA TA;")

    def test_impl_ascr3(self):
        self.compare_command("SELECT '19.43' AS col0 FROM TA TA WHERE 'wnink' < TA.name UNION SELECT '32.82' AS col0 FROM TC TC;")

    def test_impl_ascr4(self):
        self.compare_command("SELECT TB.fullheight AS col0 FROM TB TB WHERE '1' = TB.fullname UNION SELECT '3' AS col0 FROM TC TC;")

    #si she wu ru
    def test_no_simplification_1(self):
        self.compare_command("SELECT CAST(Sub1.col2 AS INT) AS col0, Sub1.col1 + Sub1.col2 AS col1 FROM (SELECT TB.fullheight + TB.fullheight AS col0, TB.realage AS col1, 34.5 AS col2 FROM TB TB) As Sub1;")

    def test_sishewuru(self):
        self.compare_command("SELECT CAST(TC0.newheight AS INT) AS col0, -1 AS col1 FROM TC TC0,TB TB1;")

    def test_mssql_1(self):
        self.compare_command("SELECT Sub1.col0 + Sub1.col1 AS col0 FROM (SELECT TC.newage + TC.newheight AS col0, 15.9 AS col1 FROM TC TC) As Sub1;")

    def test_2_pg(self):
        self.compare_command("SELECT -25.9 + 15.9 FROM TA;")

    def test_decimal_1(self):
        self.compare_command("SELECT 84.4 AS col0, 8 AS col1, CAST(Sub1.col0 AS TEXT) AS col2 FROM (SELECT 61.0 AS col0 FROM TB TB) As Sub1;")

    def test_3_pg(self):
       self.compare_command("SELECT CAST(Sub1.col0 AS DECIMAL(10,1)) AS col0, CAST(Sub1.col0 AS TEXT) AS col1 FROM (SELECT CAST(TC.newage AS DECIMAL(10,1)) AS col0, 6 AS col1 FROM TC TC) As Sub1;")

    def test_4_pg(self):
        self.compare_command("SELECT CAST(1 AS DECIMAL(10,1)) FROM TA;")


    def test_in_0(self):
        self.compare_command("SELECT 1 FROM TA WHERE 1 IN (SELECT '1' FROM TA);")


    def test_in_01(self):
        self.compare_command("SELECT TA.age AS col0, TA.age AS col1 FROM TA TA WHERE (71.6, TA.age + TA.age, CAST(TA.height AS DECIMAL(10,1))) IN (SELECT '35.0' AS col0, 42.0 AS col1, -10 AS col2 FROM (SELECT TB.realage + TB.fullname AS col0 FROM TB TB WHERE TB.fullname + TB.realage = 75.6) As Sub1 WHERE Sub1.col0 = Sub1.col0) UNION SELECT 7 AS col0, Sub2.col0 AS col1 FROM (SELECT 'cyllv' AS col0, TC.newheight AS col1 FROM TC TC) As Sub2 WHERE (Sub2.col0 + Sub2.col0, Sub2.col0 + Sub2.col1, 5) IN (SELECT CAST(TC.newheight AS INT) AS col0, TC.newname AS col1, 9 AS col2 FROM TC TC WHERE CAST(TC.newname AS INT) < TC.newage);")


    def test_in_02(self):
        self.compare_command("SELECT 1 FROM TA WHERE '1' IN (SELECT '1' FROM TA);")

    def test_rev(self):
        self.compare_command("SELECT TA.height AS col0 FROM TA TA UNION SELECT Sub1.col1 AS col0 FROM (SELECT TC.newage + TC.newage AS col0, CAST(TC.newage AS INT) AS col1 FROM TC TC WHERE (TC.newheight + TC.newage = CAST(TC.newage AS DECIMAL(10,1)) AND CAST(TC.newname AS INT) < CAST(TC.newage AS INT))) As Sub1;")

    # def test_rev_1(self):
    #     self.compare_command("SELECT CAST(Sub1.col0 AS DECIMAL(10,1)) AS col0 FROM (SELECT 'xpkuc' AS col0, TA.age AS col1, TA.height + TA.height AS col2 FROM TA TA) Sub1 WHERE 1 = 2;")

    # def test_rev_2(self):
    #     self.compare_command("SELECT 4 AS col0, 'loyxx' AS col1, CAST(Sub1.col0 AS DECIMAL(10,1)) AS col2 FROM (SELECT '12.3' AS col0 FROM TA TA WHERE (TA.height + TA.height = TA.height AND 44.5 < TA.height)) Sub1 WHERE CAST(Sub1.col0 AS INT) = CAST(Sub1.col0 AS DECIMAL(10,1));")

    def test_rev_3(self):
        self.compare_command("SELECT 1 FROM (SELECT name + age AS col0 FROM TA WHERE CAST(age AS FLOAT) = 1.1) Sub1 WHERE Sub1.col0 = Sub1.col0 + 1;")


    # def test_rev_4(self): ## here
    #     self.compare_command("SELECT CAST(Sub1.col1 AS INT) AS col0 FROM (SELECT 'vxyjv' AS col1 FROM TC WHERE 1 = 2) Sub1;")

    # def test_rev_6(self):
    #     self.compare_command("SELECT CAST(R.A AS INT) AS col0 FROM (SELECT 'foo' AS A FROM TC WHERE 1 = 2) R")

    def test_rev_5(self):
        self.compare_command("SELECT 1 FROM (SELECT name + 1 AS col0 FROM TA WHERE CAST(age AS FLOAT) = 1.1) Sub1 WHERE Sub1.col0 = Sub1.col0 + 1;")


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
            self.compare_command(generate("Postgres", simplification), simplification)
        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestPostgres, test_name, gen())
    #globals()[test_multi.__name__] = test_multi


if __name__ == "__main__":

    unittest.main()
































































































    # def test_newtablename_bigger_than_5(self):
    #     self.compare_command("SELECT CAST(C0.newheight AS INT) AS col0 FROM TC C0,TA A100,TA C101,TA B110,TC A111;")

    # def test_fail_decimal():
    #     compare_command("SELECT name,11.453018804940507,POWER(91.77049935666511,22.78334446441822) FROM TA WHERE NOT (POWER(3.428568527962006,'28.097640171996517') = 3.5573715304403675);")

    # def test_fail_sqrt_string():
    #     compare_command("(SELECT C.realage FROM "
    #                     "B AS TC WHERE NOT (POWER('16.90868110073438',1.9728588917385492) < POWER(6.418129048518262,98.06506976990222))) "
    #                     "INTERSECT (SELECT 70.01342455252092 FROM TA AS TA WHERE SQRT('wkkhl') < POWER(3.0782525408450057,45.697574742986056));")

    # def test_fail_intersect_same_colnum():
    #     compare_command("(SELECT SQRT(42.06525965511361) FROM B AS B WHERE NOT (POWER('28.062225859159174',60.58112831686804) = POWER('63.786872085110204',49.715936111892944))) "
    #                     "INTERSECT (SELECT A0.name,'gdzay',A0.age FROM TA AS A0,(SELECT SQRT('54.30729971626571') "
    #                     "FROM B AS C1 WHERE NOT (C1.fullname < '70.96988145036387')) As Sub9);")
    #
    # def test_fail_union_trans_q():
    #     compare_command("(SELECT SQRT('9.018141359146503'),'1.5859504061799434',SQRT('7.367828906754258') FROM TA AS B) "
    #                     "UNION "
    #                     "(SELECT '5.343833277778226','vcuck',SQRT(2.6075723646668103) FROM "
    #                     "(SELECT POWER(3.249909520109604,6.285119629266114),POWER(9.786045390127375,'4.492194203503365') FROM B AS B) As Sub1);")

# with open("fail_postgres.txt", "r") as file:
#    sql_commands = [q.strip() for q in file.read().split(';')[:-1] if q.strip()]


# for i, command in enumerate(sql_commands):
#     def test_fail(command = command):
#         compare_command(command)
#
#     test_fail.__name__ = f"test_fail_query_{i+1}"
#     globals()[test_fail.__name__] = test_fail


# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,CAST(Sub1.col00 AS float) AS cola
# FROM (SELECT B.newage AS col00,B.newname AS col01,2 AS cola
# FROM TC AS B) As Sub1
# WHERE Sub1.col00 + Sub1.cola = 12.86 AND CAST(Sub1.col01 AS float) < CAST(Sub1.cola AS float);
#
# SELECT B.name AS col00,B.age AS col01,60.47 AS cola
# FROM TA AS B
# WHERE CAST(B.name AS float) = CAST(B.name AS float) OR B.age = B.age;
#
# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,CAST(Sub1.col01 AS float) AS cola
# FROM (SELECT C.fullname AS col00,C.realage AS col01,4 AS cola
# FROM B AS C
# WHERE CAST(C.fullname AS float) = CAST(C.realage AS float) OR CAST(C.realage AS float) = '1') As Sub1
# WHERE CAST(Sub1.cola AS float) = CAST(Sub1.cola AS float) AND Sub1.col01 = Sub1.col01 + Sub1.cola;
#
# SELECT A.name AS col00,A.age AS col01,'zcpvl' AS cola
# FROM TA AS A
# WHERE CAST(A.age AS float) < CAST(A.name AS float) OR 1 < CAST(A.age AS float);
#
# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,B1.newage AS col20,B1.newname AS col21,92.3 AS cola
# FROM (SELECT B0.name AS col00,B0.age AS col01,72.92 AS cola
# FROM TA AS B0
# WHERE '0' = CAST(B0.age AS float) OR '52.15' = CAST(B0.age AS float)) As Sub1,C AS B1
# WHERE CAST(B1.newname AS float) < CAST(B1.newname AS float) AND Sub1.col01 < CAST(B1.newname AS float);
#
# SELECT C0.newage AS col00,C0.newname AS col01,A100.newage AS col10,A100.newname AS col11,A101.name AS col20,A101.age AS col21,C110.newage AS col30,C110.newname AS col31,A111.newage AS col40,A111.newname AS col41,2 AS cola
# FROM TC AS C0,C AS A100,A AS A101,C AS C110,C AS A111
# WHERE 27.23 = CAST(A111.newname AS float) AND C0.newage + A111.newage < A100.newage;
#
# SELECT A000.name AS col00,A000.age AS col01,C001.fullname AS col10,C001.realage AS col11,A010.name AS col20,A010.age AS col21,C011.fullname AS col30,C011.realage AS col31,Sub1.col00 AS col40,Sub1.col01 AS col41,Sub1.cola AS col50,5 AS cola
# FROM TA AS A000,B AS C001,A AS A010,B AS C011,(SELECT A1.name AS col00,A1.age AS col01,'36.05' AS cola
# FROM TA AS A1
# WHERE A1.age + A1.age = CAST(A1.age AS float) AND CAST(A1.name AS float) < A1.age) As Sub1;
#
# SELECT C.fullname AS col00,C.realage AS col01,56.45 AS cola
# FROM B AS C
# WHERE CAST(C.fullname AS float) = C.realage OR CAST(C.realage AS float) = C.realage;
#
# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,'55.33' AS cola
# FROM (SELECT B.fullname AS col00,B.realage AS col01,17.41 AS cola
# FROM B AS B
# WHERE B.realage = CAST(B.fullname AS float)) As Sub1
# WHERE Sub1.cola = '74.61' AND Sub1.cola < CAST(Sub1.col01 AS float);
#
# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,'6' AS cola
# FROM (SELECT A.fullname AS col00,A.realage AS col01,'0' AS cola
# FROM B AS A) As Sub1
# WHERE CAST(Sub1.col00 AS float) = CAST(Sub1.cola AS float) AND CAST(Sub1.col00 AS float) = Sub1.col01;
#
# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,B01.fullname AS col20,B01.realage AS col21,C1.newage AS col30,C1.newname AS col31,CAST(Sub1.col01 AS float) AS cola
# FROM (SELECT C00.newage AS col00,C00.newname AS col01,35.53 AS cola
# FROM TC AS C00) As Sub1,B AS B01,C AS C1
# WHERE CAST(C1.newname AS float) = Sub1.cola + Sub1.cola AND CAST(C1.newname AS float) = 39.17;
#
# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,'rtcgy' AS cola
# FROM (SELECT A.fullname AS col00,A.realage AS col01,8 AS cola
# FROM B AS A
# WHERE CAST(A.fullname AS float) < A.realage OR CAST(A.fullname AS float) = CAST(A.fullname AS float)) As Sub1
# WHERE Sub1.cola = Sub1.cola + Sub1.cola;
#
# SELECT C.fullname AS col00,C.realage AS col01,'58.4' AS cola
# FROM B AS C
# WHERE CAST(C.realage AS float) = CAST(C.fullname AS float) AND CAST(C.fullname AS float) = '8';
#
# SELECT Sub1.col00 AS col00,Sub1.col01 AS col01,Sub1.cola AS col10,60.81 AS cola
# FROM (SELECT A.newage AS col00,A.newname AS col01,60.13 AS cola
# FROM TC AS A
# WHERE CAST(A.newname AS float) = 79.14 OR A.newage < 65.5) As Sub1;
#
# SELECT B.fullname AS col00,B.realage AS col01,'cjnvs' AS cola
# FROM B AS B
# WHERE CAST(B.fullname AS float) < B.realage AND CAST(B.realage AS float) = B.realage + B.realage;

# SELECT A.fullname AS col00,A.realage AS col01,61.8 AS cola
# FROM B AS A
# WHERE CAST(A.fullname AS float) = CAST(A.realage AS float) AND 1 = CAST(A.fullname AS float)
# UNION
# SELECT B.name AS col00,B.age AS col01,10 AS cola
# FROM TA AS B
# WHERE 10 = B.age AND '9' < CAST(B.name AS float);

# SELECT 3 AS col
# FROM (SELECT B.fullname AS col0,B.realage AS col1
# FROM B AS B
# WHERE 5 = CAST(B.fullname AS float) AND B.fullname < '42.29') As Sub1;







# SELECT '89.48' AS col0,9 AS col1
# FROM (SELECT CAST(A00.name AS float) AS col
# FROM TA AS A00) As Sub1,A AS B01,B AS B1;
#
# SELECT '52.09' AS col
# FROM B AS A0,(SELECT CAST(A1.fullname AS float) AS cola,'imfpk' AS colb,A1.realage AS colc
# FROM B AS A1) As Sub1;
#
# SELECT 8 AS col
# FROM (SELECT B0.realage + B0.realage AS col0,CAST(B0.fullname AS float) AS col1
# FROM B AS B0) As Sub1,C AS B10,B AS C110,B AS A111;
#
# SELECT 0 AS col
# FROM TA AS B000,C AS C001,(SELECT CAST(B01.fullname AS float) AS col0,CAST(B01.fullname AS float) AS col1
# FROM B AS B01) As Sub1,A AS B1
# EXCEPT
# SELECT CAST(C.realage AS float) AS col
# FROM B AS C;
#
#
# SELECT 'lflxm' AS col
# FROM (SELECT CAST(A0.fullname AS float) AS col0,A0.fullname AS col1
# FROM B AS A0) As Sub1,C AS B1;
#
# SELECT 75.87 AS col0,A10.newname AS col1
# FROM (SELECT B00.age AS col0,CAST(B00.name AS float) AS col1
# FROM TA AS B00) As Sub1,A AS B010,A AS A011,C AS A10,A AS C11;
#
# SELECT 9 AS col
# FROM (SELECT B.name AS cola,B.age + B.age AS colb,CAST(B.name AS float) AS colc
# FROM TA AS B) As Sub1;



#
# SELECT SQRT(2)
# FROM TC AS C0,(SELECT C1.realage
# FROM B AS C1) As Sub1
# UNION
# SELECT SQRT(93.4)
# FROM TA AS B;
#
# SELECT SQRT(6.66)
# FROM TC AS B
# UNION
# SELECT POWER('4',1)
# FROM (SELECT POWER('91.89','6'),A.fullname
# FROM B AS A) As Sub1;
#
# SELECT SQRT(1)
# FROM B AS A
# UNION
# SELECT SQRT(29.17)
# FROM B AS C;
#
# SELECT POWER(66.37,3)
# FROM TA AS A0,C AS C1
# UNION
# SELECT SQRT(3)
# FROM (SELECT 6,'mupyc'
# FROM B AS B0) As Sub1,C AS C10,B AS C110,C AS A111;
#
# SELECT SQRT('95.14')
# FROM TA AS B
# UNION
# SELECT SQRT(87.74)
# FROM TC AS A;
#
# SELECT SQRT(7),C.name,SQRT(8)
# FROM TA AS C
# WHERE C.name < C.name OR C.age = SQRT('97.61')
# UNION
# SELECT A.newname,A.newage,A.newage
# FROM TC AS A
# WHERE SQRT(61.85) = SQRT(9);
#
# (SELECT SQRT(38.76),SQRT(7)
# FROM B AS B)
# UNION
# (SELECT SQRT(5),POWER(0,'10')
# FROM (SELECT POWER(8,'7'),POWER(78.1,'4')
# FROM TA AS A
# WHERE NOT (POWER(3,'92.61') < SQRT(11.83))) As Sub1);
#
# (SELECT POWER(21.84,'62.0')
# FROM (SELECT SQRT(34.07),C.newage,'nubin'
# FROM TC AS C) As Sub1)
# UNION
# (SELECT POWER('8',9)
# FROM TC AS A);

# (SELECT 15.12,5
# FROM (SELECT SQRT(3.16),POWER('72.69','2')
# FROM TA AS C0) As Sub1,(SELECT 17.18
# FROM TC AS B1
# WHERE B1.newname < '10' AND 10 = B1.newage) As Sub2)
# UNION
# (SELECT SQRT(16.07),C.fullname
# FROM B AS C
# WHERE C.realage < SQRT('10') AND POWER(81.29,64.46) < POWER(75.85,'21.65'));
#
# (SELECT SQRT('38.45'),SQRT(2)
# FROM TA AS A
# WHERE 'twtik' < A.name OR '83.0' < SQRT('77.83'))
# INTERSECT
# (SELECT '12.14',C000.name
# FROM TA AS C000,B AS C001,A AS B01,A AS A1
# WHERE POWER(3,'9') = '75.59');
#
#
# (SELECT B.name
# FROM TA AS B
# WHERE POWER(24.86,63.25) = B.age)
# INTERSECT
# (SELECT B.age
# FROM TA AS B
# WHERE POWER('3','67.0') = SQRT(2));
#
#
# (SELECT SQRT(4)
# FROM (SELECT SQRT('10'),POWER('6',24.05),'10'
# FROM B AS A
# WHERE NOT (A.fullname = 'ubcyq')) As Sub1)
# UNION
# (SELECT POWER(19.05,8)
# FROM B AS C);
#
# (SELECT B.fullname
# FROM B AS B
# WHERE NOT (SQRT(3) < B.realage))
# INTERSECT
# (SELECT POWER(48.87,2.29)
# FROM TA AS A
# WHERE A.age < 10);
#
# SELECT 60.23
# FROM (SELECT C0.age,C0.age
# FROM TA AS C0
# WHERE POWER(7,47.7) = '3' AND 'zehri' = C0.name) As Sub1,C AS A1
# WHERE SQRT('7') = A1.newname;
#
# (SELECT C100.realage
# FROM (SELECT POWER(3,7),POWER('14.78',64.42),'6'
# FROM B AS B00
# WHERE '8' = SQRT(7)) As Sub1,C AS B010,A AS C011,B AS C100,A AS A101,A AS C11
# WHERE NOT (POWER(11.65,8) < B010.newname))
# INTERSECT
# (SELECT POWER(3,'6.62')
# FROM TC AS A);
#
#
# (SELECT SQRT('2')
# FROM TA AS B)
# UNION
# (SELECT POWER(3,22.95)
# FROM (SELECT SQRT(52.3)
# FROM TC AS B) As Sub1);
#
# (SELECT POWER(5.82,71.09),'jzigo'
# FROM TA AS A)
# UNION
# (SELECT SQRT(6),C0.newname
# FROM TC AS C0,B AS C100,C AS B101,C AS C11
# WHERE SQRT(7) = 5 OR C11.newage = 6);
#
# (SELECT A.age,POWER(0,62.82),SQRT(18.17)
# FROM TA AS A)
# UNION
# (SELECT 0,POWER(0,3),POWER('6',41.27)
# FROM (SELECT 3
# FROM B AS B0
# WHERE 5 < '3' AND 8 < '5') As Sub1,B AS A1
# WHERE 6 < A1.fullname);
#
# (SELECT POWER(0,5),7.82
# FROM B AS C0,B AS A1
# WHERE NOT (33.52 < POWER(3,10)))
# UNION
# (SELECT B000.newname,SQRT('7')
# FROM TC AS B000,C AS C001,C AS C01,C AS B10,(SELECT 72.38
# FROM B AS C11
# WHERE SQRT(22.58) = SQRT('38.55')) As Sub1
# WHERE 3 = SQRT(33.72) OR SQRT('10') = C001.newname);
#
# SELECT C101.newage,POWER(95.68,93.0)
# FROM (SELECT 8,11.26,A0.fullname
# FROM B AS A0
# WHERE POWER(9,'92.43') = A0.realage) As Sub1,B AS A100,C AS C101,A AS C11
# WHERE A100.realage < POWER(53.78,'6') AND POWER('36.15',8) < C11.name;
#
# (SELECT A.fullname
# FROM B AS A
# WHERE 41.19 = 1 AND A.fullname = '6')
# INTERSECT
# (SELECT 37.37
# FROM (SELECT SQRT(57.54)
# FROM TA AS A00
# WHERE NOT (1 < A00.age)) As Sub1,(SELECT B01.name,'40.39'
# FROM TA AS B01) As Sub2,B AS C100,A AS B101,(SELECT A11.realage
# FROM B AS A11
# WHERE '75.83' = '10' OR 0 < SQRT('5')) As Sub3
# WHERE SQRT(3) = SQRT('0') OR '14.34' < '44.87');
#
# (SELECT SQRT(9)
# FROM (SELECT 'ivcuh'
# FROM B AS C) As Sub1)
# UNION
# (SELECT POWER(46.11,34.36)
# FROM TC AS C00,C AS A010,A AS A011,C AS A1);
#
# (SELECT SQRT(8.12)
# FROM TA AS C)
# UNION
# (SELECT SQRT(9)
# FROM TA AS A);
#
#
# (SELECT A0.newname,64.38,'1'
# FROM TC AS A0,B AS A1
# WHERE A1.realage < SQRT(10))
# UNION
# (SELECT A.age,A.name,6.17
# FROM TA AS A
# WHERE 'jrcwc' < A.name);
#
# (SELECT C.fullname,C.realage,SQRT(92.66)
# FROM B AS C
# WHERE 'ydoiw' < '16.23' OR POWER(6,10.98) = C.realage)
# INTERSECT
# (SELECT C.fullname,'1',C.fullname
# FROM B AS C
# WHERE POWER('61.57',18.97) < C.realage OR POWER('80.56',48.06) < SQRT(7));
#
#
# (SELECT POWER(7,47.67),87.53,62.09
# FROM B AS A0,A AS C1)
# UNION
# (SELECT SQRT('81.71'),POWER('65.75',0.56),SQRT(4)
# FROM (SELECT A.fullname,6,4
# FROM B AS A
# WHERE 95.06 < POWER(17.28,19.24) OR 6 = SQRT('8')) As Sub1);
#
# (SELECT SQRT(4),SQRT(61.35)
# FROM (SELECT POWER(4,'8')
# FROM TA AS A) As Sub1)
# UNION
# (SELECT POWER(5,62.64),POWER('10',7)
# FROM (SELECT A.newname,POWER(32.45,'2'),SQRT('1')
# FROM TC AS A
# WHERE '2' < A.newage AND A.newname < A.newname) As Sub2);
#
# (SELECT SQRT(8),POWER('12.91',38.6)
# FROM B AS A0,A AS A1
# WHERE A0.realage = SQRT(1) OR 10 = SQRT(40.67))
# UNION
# (SELECT SQRT(12.8),POWER('57.29',10)
# FROM (SELECT B.newage,POWER(3,5)
# FROM TC AS B) As Sub1);
#
# SELECT A010.fullname
# FROM TC AS A000,A AS C001,B AS A010,A AS B011,(SELECT 6,10.63
# FROM TA AS B1
# WHERE POWER(41.83,'78.68') = SQRT(10)) As Sub1
# WHERE NOT (72.51 < B011.name);
#
# (SELECT POWER('81.31','32.63'),A.realage
# FROM B AS A)
# UNION
# (SELECT POWER('3',96.93),POWER(2,5)
# FROM (SELECT C.fullname
# FROM B AS C) As Sub1
# WHERE NOT (SQRT(3) = SQRT(10)));
#
# (SELECT POWER(10.66,8),A.age,A.name
# FROM TA AS A)
# UNION
# (SELECT POWER(5,'86.14'),SQRT('45.9'),'7'
# FROM (SELECT A.newname,SQRT(2.22),33.05
# FROM TC AS A) As Sub1);
#
# (SELECT SQRT('30.51'),1
# FROM TA AS B)
# UNION
# (SELECT POWER(33.24,10),SQRT(2)
# FROM TC AS C0,A AS B10,B AS C11);
#
# SELECT B00.age
# FROM TA AS B00,(SELECT SQRT('35.42'),POWER(7,8)
# FROM B AS A01
# WHERE A01.realage < A01.realage) As Sub1,A AS B10
#
#
# SELECT SQRT('2'),SQRT(65.26),0
# FROM (SELECT A0.newage,A0.newage,SQRT('5.49')
# FROM TC AS A0
# WHERE A0.newage < SQRT(7)) As Sub1,A AS B100,B AS B101,C AS B110,C AS B111
# WHERE NOT (B110.newname < SQRT('3'));
#
# (SELECT POWER(3,46.64)
# FROM TC AS A)
# UNION
# (SELECT POWER('9','3')
# FROM (SELECT C.name,5
# FROM TA AS C) As Sub1);
#
# (SELECT A01.name
# FROM TC AS B000,B AS A001,A AS A01,A AS C10,(SELECT 'tnchh'
# FROM B AS A11
# WHERE POWER(44.86,'78.16') < '6') As Sub1)
# INTERSECT
# (SELECT SQRT('18.32')
# FROM B AS A0,A AS A100,B AS A101,(SELECT SQRT(3),C11.realage,SQRT(10)
# FROM B AS C11
# WHERE NOT (SQRT(3) < '40.43')) As Sub2
# WHERE A0.realage < SQRT('39.46') OR SQRT(7) = POWER(6,90.56));
#
# SELECT A010.name
# FROM TC AS C000,A AS A001,A AS A010,C AS B011,(SELECT A1.age,A1.name
# FROM TA AS A1
# WHERE NOT (5 < POWER(7,47.37))) As Sub1
# WHERE SQRT(1) < B011.newname AND A001.name < B011.newage;
#
# (SELECT POWER(6,10.57)
# FROM B AS C)
# UNION
# (SELECT POWER('9',7)
# FROM (SELECT SQRT(9),B.name,'tlzfb'
# FROM TA AS B
# WHERE POWER(25.73,4) < B.age AND SQRT(9.26) = B.age) As Sub1);
#
# (SELECT POWER('8',1),2,SQRT(2)
# FROM B AS C)
# UNION
# (SELECT SQRT('53.6'),3,POWER('88.08',20.3)
# FROM TC AS B);
#
# (SELECT SQRT('5')
# FROM TC AS B)
# UNION
# (SELECT POWER(41.49,9)
# FROM B AS C);
#
# (SELECT POWER('8','1'),POWER(6,'4'),SQRT(8)
# FROM B AS C
# WHERE C.realage = 56.59)
# UNION
# (SELECT '2',POWER(6,63.91),POWER(6,85.9)
# FROM (SELECT SQRT(9)
# FROM TA AS C00) As Sub1,B AS A01,(SELECT A1.fullname,'9'
# FROM B AS A1) As Sub2);
#
# (SELECT SQRT('92.79'),'4'
# FROM (SELECT SQRT(25.19)
# FROM TA AS C) As Sub1)
# UNION
# (SELECT SQRT(6.21),96.72
# FROM (SELECT '31.18'
# FROM B AS C) As Sub2);
#
# (SELECT B1.newname,0
# FROM TC AS C0,C AS B1
# WHERE NOT (SQRT(8) < 5))
# INTERSECT
# (SELECT A.newage,81.08
# FROM TC AS A
# WHERE A.newage = POWER(3,'17.77'));
#
# (SELECT SQRT(3),POWER(45.08,46.43)
# FROM B AS A
# WHERE NOT (77.55 < '47.27'))
# UNION
# (SELECT POWER(0.17,'63.64'),POWER('7',4)
# FROM TA AS B);
#
#
# (SELECT 1,POWER('61.12','6'),A10.newage
# FROM TA AS C0,C AS A10,B AS A11)
# UNION
# (SELECT A1.realage,78.04,SQRT(1)
# FROM (SELECT C0.fullname
# FROM B AS C0
# WHERE SQRT(43.6) = SQRT(34.74)) As Sub1,B AS A1
# WHERE A1.fullname = SQRT(57.35));
#
# (SELECT SQRT(5),SQRT(3.32)
# FROM B AS B)
# UNION
# (SELECT POWER(57.54,77.56),POWER(2,'5')
# FROM B AS C0,(SELECT POWER('33.48',1),A1.fullname,'pennb'
# FROM B AS A1) As Sub1);
#
# (SELECT SQRT(0),POWER('2',22.79),A01.age
# FROM (SELECT '55.0',POWER('7','80.59')
# FROM TC AS B00) As Sub1,A AS A01,B AS B100,B AS C101,A AS B11)
# UNION
# (SELECT POWER(22.67,28.54),SQRT(9),SQRT(0)
# FROM B AS A);
#
# (SELECT 6,POWER(30.14,'8.65'),SQRT('0')
# FROM B AS C)
# UNION
# (SELECT SQRT('7'),POWER(10,1),POWER(2,78.47)
# FROM B AS B
# WHERE B.realage = SQRT(3));
#
# SELECT 'yvaxu'
# FROM TA AS A00,B AS C01,(SELECT SQRT('6'),POWER(38.34,55.82)
# FROM TA AS A1
# WHERE POWER('8','10') < 7) As Sub1
# WHERE 8 = A00.name AND SQRT('7') = POWER('99.68','84.72');
#
# (SELECT SQRT(1)
# FROM TA AS C
# WHERE SQRT('32.64') = SQRT('80.58'))
# UNION
# (SELECT POWER(2.41,10)
# FROM B AS A);




# def test_simple_query():
#     compare_command("SELECT '1' FROM TA UNION SELECT '1' FROM A;")
# # #
# def test_syntax_error_command():
#     compare_command("SELECT '1.1' FROM TA union select 1 from A;")
#
# def test_nested_query():
#     compare_command("SELECT power('1', 1) FROM (SELECT 2 FROM TA WHERE 10 = 10) AS sub;")

# def test_multiple():
#     i = 0
#     while i <= 20:
#         print(f"{i + 1}'s test:")
#         i = i + 1
#         def test_generator():
#             compare_command(generate())
#

# def test_generator_example_product_trans():
#     compare_command("SELECT '33.88360708454309' FROM C, B WHERE 'cnncw' < 'zvbrn';")
#
# def test_generator_example_dbt_names():
#     compare_command("SELECT age FROM B WHERE 14.783000506926037 = 9.580409429003932;")
#
# def test_generator_example_same_col_diff_order():
#     compare_command("SELECT 'dozxz' FROM C,A,B WHERE 'zxrcu' < '3.5903328854777095';")
# def test_generator_example_overload():
#     compare_command("SELECT '90.46931814710045',age AS POWER('otolz',40.696730675611484),2.0087167524899807 AS name FROM TA WHERE age = POWER(43.68155080943935,96.12442231652265) AND SQRT('4.7648881328852255') = POWER(6.315466585027152,'41.63292365308067');")

# SELECT age FROM B WHERE 14.783000506926037 = 9.580409429003932;
# SELECT '33.88360708454309' FROM C, B WHERE 'cnncw' < 'zvbrn';
# SELECT 'dozxz' FROM C,A,B WHERE 'zxrcu' < '3.5903328854777095';
# SELECT 87.03025933753857 FROM C,B,A WHERE '32.26440549231785' < '37.213775997199235';
# SELECT '90.46931814710045',age AS POWER('otolz',40.696730675611484),2.0087167524899807 AS name FROM TA WHERE age = POWER(43.68155080943935,96.12442231652265) AND SQRT('4.7648881328852255') = POWER(6.315466585027152,'41.63292365308067');




# for i, command in enumerate(sql_commands):
#     def test_postgres(postgresql_conn_old, command = command):
#         conn = psycopg2.connect(**postgresql_conn_old)
#         # Execute each query one by one
#         cur = conn.cursor()
#         cur.execute(command)
#         rows = cur.fetchall()
#         column_names = [desc[0] for desc in cur.description]
#         parsed = parse_command(command)
#         typecheck(dbt, parsed, Postgres())
#         mytable = (parsed.trans(dbt, Postgres())).run(db, Postgres())
#         print(command)
#         print(parse_command(command))
#         print("our result:")
#         print(mytable)
#         print("postgres result:")
#         print(column_names)
#         for row in rows:
#             print(row)
#         assert Engine().Compare(mytable.rows, rows, Postgres())
#
#         cur.close()
#         conn.close()
#     test_postgres.__name__ = f"test_postgresql_query_{i + 1}"
#     globals()[test_postgres.__name__] = test_postgres

    # def test_run():
    #     # assert Engine().Compare([[1],[0],[1]], [(1,),(1,),(0,)], Postgres())
    #     # assert Engine().Compare([[1], [2], [1]], [(1,), (2,), (2,)], Postgres())
    #     # assert Engine().Compare([[1,1], [2,1], [1]], [(1,1), (2,), (2,1)], Postgres())
    #     # assert Engine().Compare([[1, 1], [2, 1], [2]], [(1, 1), (2,), (2, 1)], Postgres())
    #     # assert Engine().Compare([[1, 1], [2, True], [2]], [(1, 1), (2,), (2, 1)], Mysql())
    #     # assert Engine().Compare([[1, 1], [2, True], [False]], [(1, 1), (0,), (2, 1)], Mysql())
    #     assert Engine().Compare([[1.0, 1], [2, True], [False]], [(1, 1), (0,), (2, 1)], Mysql())













