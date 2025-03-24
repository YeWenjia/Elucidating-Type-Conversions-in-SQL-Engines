from interpreter.syntax.engine.Engine import Engine
from interpreter.queryGenerator import *
import unittest

from interpreter.syntax.type.RelationType import RelationType, NameType


class TestEngine(unittest.TestCase):
    db = {}
    dbt = {}



    @classmethod
    def populateDatabase(cls):
        cur = cls.conn.cursor()
        cur.execute("SELECT name, height, age From TA")
        rows_ta = [list(r) for r in cur.fetchall()]
        for row in rows_ta:
            for i, v in enumerate(row):
                cv = BValue(v)
                cv.unknown = False
                row[i] = cv
        cur.execute("SELECT realage, fullname, fullheight From TB")
        rows_tb = [list(r) for r in cur.fetchall()]
        for row in rows_tb:
            for i, v in enumerate(row):
                cv = BValue(v)
                cv.unknown = False
                row[i] = cv
        cur.execute("SELECT newage, newheight, newname From TC")
        rows_tc = [list(r) for r in cur.fetchall()]
        for row in rows_tc:
            for i, v in enumerate(row):
                cv = BValue(v)
                cv.unknown = False
                row[i] = cv


        cls.db = {
            "TA": Table(["name", "height", "age"], rows_ta),
            "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
            "TC": Table(["newage", "newheight", "newname"], rows_tc)
        }

        cls.dbt = {
            "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
            "TB": RelationType(
                [NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
            "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
        }

        print(cls.db['TC'].rows)

    def write_string_to_file(self, string, filename):
        with open(filename, 'a') as file:
            file.write(string + '\n')

    def parse_command(self,command):
        parsed = sqlparse.parse(command)
        statement = parsed[0]  # assume there's only one statement per query
        query_object = parse_select(statement)
        return query_object

    def compare_command(self,command: str, simplification = True):
        rows = []
        their_error = False
        our_error = False
        # Execute each query one by one
        print(command)
        # self.write_string_to_file(command, 'output.txt')
        cur = self.conn.cursor()

        # We first run it in the interpreter
        print("parsed:")
        parsed = self.parse_command(command)
        print(self.parse_command(command))
        mytable = []
        try:
            parsed.typecheck(self.dbt, self.engine)
            print("pass type checker")
            print("transed:")
            transd = parsed.trans(self.dbt, self.engine)
            print(transd)
            mytable = transd.run(self.db, self.engine)
            print("our result:")
            print(mytable)
        except Exception as e:
            our_error = True
            print("Error:", e)
            # raise e

        if not simplification and our_error:
            return

        # now we run it in the engine
        try:
            # query = command.replace(";", "")
            if self.engine.tag == "Oracle":
                command = command.replace(";", "")
            print([command])
            cur.execute(command)
            column_names = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            print("ENGINE result:")
            print(column_names)
            for row in rows:
                print(row)
        except Exception as e:
            print("Error:", e)
            their_error = True
        self.conn.rollback()

        if not simplification and their_error and self.engine.tag == "Oracle":
            return

        if not simplification and their_error and self.engine.tag == "Postgres":
            return

        if not our_error and not their_error and self.engine.tag == "Oracle":
            assert Engine().Compare(mytable.rows, rows, self.engine)

        elif not our_error and not their_error and self.engine.tag == "Postgres":
            assert Engine().Compare(mytable.rows, rows, self.engine)

        elif not our_error:
            assert Engine().Compare(mytable.rows, rows, self.engine) and (our_error == their_error)
        else:
            print("our_error")
            print(our_error)
            print("their_error")
            print(their_error)
            assert our_error == their_error

        cur.close()


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()