import yaml
import cx_Oracle
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Oracle import Oracle
from interpreter.queryGenerator import *
from test.prv.test_engine import TestEngine

import unittest



class TestOracle(TestEngine):
    @classmethod
    def setUpClass(cls):
        cls.engine = Oracle()

        with open('config.yml', 'r') as f:
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
        cls.conn = cx_Oracle.connect(**oracle_conn)

        cls.populateDatabase()

    # def test_no_res(self):
    #     self.compare_command("SELECT TA000.realage AS col0 FROM TB TA000,TC A001,TC B010,TC B011,TC A100,TC A101,TB TB11")
    #
    # def test_identifier(self):
    #     self.compare_command("SELECT 29.04 AS col0,A100.newage AS col1,1 AS col2 FROM TA A0,TC A100,TC A101,TB C110,TB A111")


    def test_except(self):
        self.compare_command("SELECT '0' AS col0 FROM TC A0,TC A1 MINUS SELECT 'riprp' AS col0 FROM TA C00,TB B01,TB C1")


    def test_fail_setop(self):
        self.compare_command("SELECT age AS col0 FROM TA WHERE age + age < age MINUS SELECT 'mgrsr' AS col0 FROM TC WHERE CAST(newname AS VARCHAR(255)) = 'zzfxt';")


    def test_bug(self):
        self.compare_command("SELECT 42.19 AS col0 FROM TA WHERE age + age < age MINUS SELECT 'tanog' AS col0 FROM TA WHERE name < '97.96';")


    def test_bug2(self):
        self.compare_command("SELECT 42.19 AS col0 FROM TA WHERE age + age < age MINUS SELECT name AS col0 FROM TA WHERE name < '97.96';")

    # excast should change in the paper
    def test_bug3(self):
        self.compare_command("SELECT CAST('hi' AS INT) FROM TA WHERE age + age < age;")

    def test_bug5(self):
        self.compare_command("SELECT CAST('hi' AS INT) FROM TA")

    def test_bug4(self):
        self.compare_command("SELECT CAST(name AS INT) FROM TA WHERE age + age < age")

    def test_bug6(self):
        self.compare_command("SELECT CAST(name AS INT) FROM TA")

    def test_tabela(self):
        self.compare_command("SELECT name FROM TA")

    def test_tabelb(self):
        self.compare_command("SELECT fullname FROM TB")

    def test_tabelc(self):
        self.compare_command("SELECT newname FROM TC")

    def test_double_col(self):
        self.compare_command("SELECT CAST(TB.fullheight AS FLOAT) AS col0 FROM TB TB WHERE 'movsg' = 28.79")

    def test_round(self):
        self.compare_command("SELECT CAST(TC.fullheight AS INT) AS col0 FROM TB TC")

    def test_float(self):
        self.compare_command("SELECT TA1.fullheight + TC0.fullheight AS col0 FROM TB TC0,TB TA1")

    def test_fail_minus(self):
        self.compare_command("SELECT 11.01 AS col0 FROM TA TA MINUS SELECT TB1.fullheight + TC0.newheight AS col0 FROM TC TC0,TB TB1;")

    def test_fail_1(self):
        self.compare_command("SELECT 11.01 AS col0 FROM TA TA;")

    def test_fail_2(self):
        self.compare_command("SELECT TB1.fullheight + TC0.newheight AS col0 FROM TC TC0,TB TB1;")

    def test_nos_o_1(self):
        self.compare_command("SELECT cast(height as VARCHAR(255)) FROM TA;")

    def test_nos_o_2(self):
        self.compare_command("SELECT cast(1.0 as VARCHAR(255)) FROM TA;")

    # def test_rev_1(self):
    #     self.compare_command("SELECT 17.5 AS col0 FROM (SELECT TB.fullname AS col0 FROM TB TB WHERE (CAST(TB.realage AS INT) = CAST(TB.fullheight AS VARCHAR(255)) OR CAST(TB.realage AS INT) = -1)) Sub1 WHERE CAST(Sub1.col0 AS FLOAT) < Sub1.col0 + Sub1.col0;")
    #
    # def test_rev_2(self):
    #     self.compare_command("SELECT TC0.newage AS col0 FROM TC TC0,TC TC1 MINUS SELECT CAST(Sub1.col0 AS INT) AS col0 FROM (SELECT TB.fullheight + TB.realage AS col0 FROM TB TB WHERE '32.7' < CAST(TB.fullheight AS INT)) Sub1 WHERE (CAST(Sub1.col0 AS VARCHAR(255)) < CAST(Sub1.col0 AS INT) AND Sub1.col0 + Sub1.col0 = 'frnjk');")

    # def test_rev_3(self):
    #     self.compare_command("SELECT 1 FROM (SELECT name + 1 AS col0 FROM TA WHERE CAST(age AS FLOAT) = 1.1) Sub1 WHERE Sub1.col0 = Sub1.col0 + 1;")

    def test_rev_4(self):
        self.compare_command("SELECT name + 1 AS col0 FROM TA WHERE CAST(age AS FLOAT) = 1.1;")

    def test_rev_5(self):
        self.compare_command("SELECT 1 FROM (SELECT name + 1 AS col0 FROM TA WHERE CAST(age AS FLOAT) = 1.1) Sub1 WHERE 1 = 2;")

    def test_rev_6(self):
        self.compare_command("SELECT 1 FROM (SELECT name + 1 AS col0 FROM TA WHERE 1=1) Sub1 WHERE Sub1.col0 = Sub1.col0 + 1;")

    # def test_rev_reply(self):
    #     self.compare_command("")

# SELECT CAST(Sub1.col1 AS VARCHAR(255)) AS col0, 'ckjjb' AS col1, Sub1.col2 AS col2 FROM (SELECT CAST(TA.height AS FLOAT) AS col0, TA.height AS col1, TA.height AS col2 FROM TA TA) Sub1 UNION SELECT '-6' AS col0, Sub2.col0 AS col1, CAST(Sub2.col0 AS INT) AS col2 FROM (SELECT 'nmbcc' AS col0 FROM TA TA WHERE (TA.age = '10' AND TA.age < TA.age + TA.age)) Sub2 WHERE 8 = Sub2.col0;


# SELECT CAST(fullname AS FLOAT) FROM TB;
# SELECT TC0.newage AS col0 FROM TC TC0,TC TC1 MINUS SELECT CAST(Sub1.col0 AS INT) AS col0 FROM (SELECT TB.fullheight + TB.realage AS col0 FROM TB TB WHERE '32.7' < CAST(TB.fullheight AS INT)) Sub1 WHERE (CAST(Sub1.col0 AS VARCHAR(255)) < CAST(Sub1.col0 AS INT) AND Sub1.col0 + Sub1.col0 = 'frnjk');

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
    def gen():
        simplification = False
        def test_multi(self):
            self.compare_command(generate("Oracle", simplification), simplification)
        return test_multi

    test_name = f"test_multi_query_{i}"
    setattr(TestOracle, test_name, gen())
    #globals()[test_multi.__name__] = test_multi


if __name__ == "__main__":

    unittest.main()
    # conn.close()






















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
# oracle_config = config['oracle']
# dsn = oracle_config['dsn']
# username = oracle_config['user']
# password = oracle_config['password']
#
#
# oracle_conn = {
#     'user': username,
#     'password': password,
#     'dsn': dsn
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
# def simpl_parse(sql_command):
#     if sql_command == 'SELECT name,age FROM TA;':
#         return Proj(Beta([Alias(Name("name"), "name"), Alias(Name("age"), "age")]), Rel("A", ["name", "age"]))
#     elif sql_command == 'SELECT name FROM TA;':
#         return Proj(Beta([Alias(Name("name"), "name")]), Rel("A", ["name", "age"]))
#     else:
#         print("queries not found!")
#
#
# def parse_command(command):
#     parsed = sqlparse.parse(command)
#     statement = parsed[0]  # assume there's only one statement per query
#     query_object = parse_select(statement)
#     return query_object
#
#
# conn = cx_Oracle.connect(**oracle_conn)
#
# cur = conn.cursor()
# cur.execute("SELECT name, height, age FROM TA")
# rows = cur.fetchall()
# for r in rows:
#     db["TA"].rows.append(list(r))
#
# print(db)
#
# cur.execute("SELECT realage, fullname, fullheight FROM TB")
# rows = cur.fetchall()
# for r in rows:
#     db["TB"].rows.append(list(r))
#
# print(db)
#
# cur.execute("SELECT newage, newheight, newname FROM TC")
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
#     # Execute each query one by one
#     # print(command)
#     cur = conn.cursor()
#     try:
#     # if 1:
#         query = command.replace(";", "")
#         print(query)
#         cur.execute(query)
#         column_names = [desc[0] for desc in cur.description]
#         rows = cur.fetchall()
#         print("oracle result:")
#         print(column_names)
#         for row in rows:
#             print(row)
#     # else:
#     except cx_Oracle.Error as e:
#         print("oracle error:", e)
#         their_error = True
#     conn.rollback()
#     print("parsed:")
#     parsed = parse_command(command)
#     print(parse_command(command))
#     try:
#         typecheck(dbt, parsed, Oracle())
#         print("type checker pass!")
#         print("transed:")
#         transd = parsed.trans(dbt, Oracle())
#         print(transd)
#         mytable = transd.run(db, Oracle())
#         print("our result:")
#         print(mytable)
#     except:
#         our_error = True
#     if not our_error:
#         if not their_error:
#             assert Engine().Compare(mytable.rows, rows, Oracle())
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
#         # if not their_error and rows == []:
#         #     their_error = True
#         assert our_error == their_error
#
#     cur.close()



# with open("fail_oracle.txt", "r") as file:
#     sql_commands = [q.strip() for q in file.read().split(';')[:-1] if q.strip()]


# for i, command in enumerate(sql_commands):
#     def test_fail(command = command):
#         self.compare_command(command, conn)
#
#     test_fail.__name__ = f"test_fail_query_{i+1}"
#     globals()[test_fail.__name__] = test_fail




