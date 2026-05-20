from interpreter.queryGenerator import *


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

db = {
    "TA": Table(["name", "height", "age"], [[BValue("Alice"), BValue(111), BValue(25)], [BValue("Bob"), BValue(222), BValue(30)]]),
    "TB": Table(["realage", "fullname", "fullheight"], [[ BValue(3),BValue("Bob"), BValue(30)], [ BValue(12), BValue("Alice"), BValue(25)]]),
    "TC": Table(["newage", "newheight", "newname"], [[BValue(30), BValue(11), BValue("Bob")], [BValue(25), BValue(13), BValue("Alice")]])
}

dbt = {
    "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
    "TB": RelationType([NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
    "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
}

rows_ta = db["TA"].rows
for row in rows_ta:
    for i, v in enumerate(row):
        cv = v
        v.unknown = False
        row[i] = cv


rows_tb = db["TB"].rows
for row in rows_tb:
    for i, v in enumerate(row):
        cv = v
        cv.unknown = False
        row[i] = cv

rows_tc = db["TC"].rows
for row in rows_tc:
    for i, v in enumerate(row):
        cv = v
        cv.unknown = False
        row[i] = cv



def run(db, query, sql):
    return query.run(db,sql)

def typecheck(dbt, query, sql):
    return query.typecheck(dbt,sql)

def trans(dbt, query, sql):
    return query.trans(dbt, sql)

# boolean value; email; changed the file

def write_string_to_file(string, filename):
    with open(filename, 'a') as file:
        file.write(string + '\n')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    for i in range(0,100000):
        q = generate("Oracle", False)
        write_string_to_file(q,'output.txt')

    # parsed = sqlparse.parse("SELECT A.col0 FROM (SELECT TC.newage AS col0 FROM TC TC UNION SELECT '0' AS col0 FROM TC TC) A WHERE A.col0 < 1;")
    # parsed = sqlparse.parse("SELECT A.age FROM TC A WHERE (1 IN (SELECT B.name FROM TC B) AND 1 < 2);")
    # parsed = sqlparse.parse(
    #     "SELECT 1 FROM TC A WHERE EXISTS (SELECT 1 FROM TC A);")
    # parsed = sqlparse.parse("SELECT A.newname FROM TC A WHERE (1, 2, 3) IN (SELECT 1, 2, 3 FROM TC B);")
    # parsed = sqlparse.parse("SELECT Sub1.col0 + Sub1.col0 AS col0 FROM (SELECT CAST(TC.newname AS INT) AS col0 FROM TC TC) As Sub1 WHERE Sub1.col0 IN (SELECT '99.3' AS col0 FROM (SELECT TC.newheight AS col0, TC.newname AS col1 FROM TC TC WHERE 'qfvyh' = 73.9) As Sub2);")
    # parsed = sqlparse.parse("SELECT newname AS col0 FROM TC WHERE (newname, 2) IN (SELECT name AS col0, 2 AS col1 FROM TA);")
    # parsed = sqlparse.parse("SELECT newname AS col0 FROM TC WHERE newname IN (SELECT name AS col0 FROM TA);") why we have in
    # parsed = sqlparse.parse("SELECT '-6' AS col0, 7.4 AS col1 FROM TB TB WHERE TB.realage + TB.realage IN (SELECT TB0.realage AS col0 FROM TB TB0,TC TC1);")
    # parsed = sqlparse.parse(
    #     "SELECT TB1.fullname + TA0.age AS col0, -7 AS col1, 41.8 AS col2 FROM TA TA0,TB TB1 WHERE (TA0.height, CAST(TA0.name AS DECIMAL(10,1)), CAST(TA0.age AS DECIMAL(10,1))) IN (SELECT Sub1.col1 + Sub1.col0 AS col0, CAST(Sub1.col0 AS DECIMAL(10,1)) AS col1, 'tmxnd' AS col2 FROM (SELECT 33.5 AS col0, 5 AS col1 FROM TB TB) As Sub1 WHERE CAST(Sub1.col0 AS TEXT) = '-5');")
    # query = "SELECT 4 AS col0 FROM TA WHERE CAST(age AS TEXT) IN (SELECT age + name AS col0 FROM TA);"
    # query = "SELECT 1 FROM TA WHERE CAST(age AS TEXT) = age + name;"
    # query = "SELECT 90.0 AS col0, CAST(Sub1.col1 AS DECIMAL(10,1)) + CAST(Sub1.col0 AS DECIMAL(10,1)) AS col1, Sub1.col1 AS col2 FROM (SELECT TA.age AS col0, TA.name AS col1 FROM TA TA) As Sub1 UNION SELECT CAST(TC1.newheight AS SIGNED) AS col0, 0 AS col1, CAST(TC1.newage AS DECIMAL(10,1)) AS col2 FROM TB TB0,TC TC1 WHERE CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) IN (SELECT Sub2.col0 AS col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.height AS DECIMAL(10,1)) AS col0 FROM TA TA WHERE CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2 WHERE CAST(Sub2.col0 AS DECIMAL(10,1)) + CAST(Sub2.col0 AS DECIMAL(10,1)) < '0');"

    ############################################### old ###############################################
    # query = "SELECT 1 AS col0 FROM TB TB0,TC TC1 " \
    #         "WHERE CAST(TC1.newage AS DECIMAL(10,1)) + CAST(TC1.newname AS DECIMAL(10,1)) " \
    #         "IN (SELECT Sub2.col0 AS col0 FROM (SELECT CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.height AS DECIMAL(10,1)) AS col0 " \
    #         "FROM TA TA WHERE CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) < TA.age) As Sub2 " \
    #         "WHERE CAST(Sub2.col0 AS DECIMAL(10,1)) + CAST(Sub2.col0 AS DECIMAL(10,1)) < '0');"
    # parsed = sqlparse.parse(query);
    # statement = parsed[0]
    # tokens = statement.tokens
    # query_object = parse_select(tokens)
    # print("parsed:")
    # print(query_object)
    # t = typecheck(dbt, query_object, Sqlite())
    # print("passtypechecker")
    # query_object = trans(dbt, query_object, Sqlite())
    # print("transd:")
    # print(query_object)
    # print("result:")
    # print(run(db, query_object, Sqlite()))
    ###############################################  ############################################### ###############################################


# SELECT TB1.fullname + TA0.age AS col0, -7 AS col1, 41.8 AS col2 FROM TA TA0,TB TB1 WHERE (TA0.height, CAST(TA0.name AS DECIMAL(10,1)), CAST(TA0.age AS DECIMAL(10,1))) IN (SELECT Sub1.col1 + Sub1.col0 AS col0, CAST(Sub1.col0 AS DECIMAL(10,1)) AS col1, 'tmxnd' AS col2 FROM (SELECT 33.5 AS col0, 5 AS col1 FROM TB TB) As Sub1 WHERE CAST(Sub1.col0 AS TEXT) = '-5');

# SELECT CAST(Sub1.col0 AS TEXT) AS col0 FROM (SELECT CAST(TA.height AS TEXT) AS col0 FROM TA TA) As Sub1 WHERE Sub1.col0 IN (SELECT TC.newheight AS col0 FROM TC TC);
# SELECT -5 AS col0, TC.newage AS col1 FROM TC TC WHERE CAST(TC.newage AS TEXT) IN (SELECT CAST(TA1.age AS INT) AS col0 FROM TC TC0,TA TA1);
# SELECT 4 AS col0 FROM TA TA WHERE CAST(TA.age AS TEXT) IN (SELECT TA1.age + TA0.name AS col0 FROM TA TA0,TA TA1);









# See PyCharm help at https://www.jetbrains.com/help/pycharm/
