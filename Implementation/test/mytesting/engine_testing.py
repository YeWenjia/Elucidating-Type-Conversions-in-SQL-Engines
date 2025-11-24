from interpreter.syntax.engine.Engine import Engine
from interpreter.queryGenerator import *
import unittest

from interpreter.syntax.type.RelationType import RelationType, NameType


class TestEngine(unittest.TestCase):
    db = {}
    dbt = {}

    stats = {
        'total_tests': 0,
        'our_error': 0,
        'their_error': 0,
        'compare_false': 0,
        # 'both_success': 0
    }

    error_ids = {
        'our_error_ids': [],
        'their_error_ids': [],
        'compare_false_ids': []
    }

    @classmethod
    def populateDatabase(cls, use_decimal=True):
        cur = cls.conn.cursor()
        cur.execute("SELECT name, height, age From TA")
        rows_ta = [list(r) for r in cur.fetchall()]
        for row in rows_ta:
            for i, v in enumerate(row):
                cv = BValue(v, use_decimal)
                cv.unknown = False
                row[i] = cv
        cur.execute("SELECT realage, fullname, fullheight From TB")
        rows_tb = [list(r) for r in cur.fetchall()]
        for row in rows_tb:
            for i, v in enumerate(row):
                cv = BValue(v, use_decimal)
                cv.unknown = False
                row[i] = cv
        cur.execute("SELECT newage, newheight, newname From TC")
        rows_tc = [list(r) for r in cur.fetchall()]
        for row in rows_tc:
            for i, v in enumerate(row):
                cv = BValue(v, use_decimal)
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
            "TC": RelationType(
                [NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
        }

        # print(cls.db['TC'].rows)

    def write_string_to_file(self, string, filename):
        with open(filename, 'a') as file:
            file.write(string + '\n')

    def parse_command(self, command):
        parsed = sqlparse.parse(command)
        statement = parsed[0]  # assume there's only one statement per query
        query_object = self.parser.parse_select(statement)
        return query_object

    def compare_command(self, command: str, simplification=False, test_index = None):
        rows = []
        their_error = False
        our_error = False
        compare_result = True

        self.__class__.stats['total_tests'] += 1
        current_test_id = self.__class__.stats['total_tests']

        # Execute each query one by one
        print(command)
        if test_index is not None:
            print(f"[Test Index: {test_index}]")
        # self.write_string_to_file(command, 'output.txt')
        cur = self.conn.cursor()

        # We first run it in the interpreter
        parsed = self.parse_command(command)
        print("Our parsed result is:", parsed)
        mytable = []
        try:
            TQ = self.engine.typechecker.typecheck_query(self.dbt, parsed)
            T = TQ[0]
            qp = TQ[1]
            print("type is :", T)
            print("Translation result is: ", qp)
            mytable = self.engine.run.run_query(self.db, qp)
            print("Our running result is: ", mytable)
        except Exception as e:
            our_error = True
            print("Our Error is: ", e)
            # raise e

        ############################################ for journal
        # if not simplification and our_error:
        #     return
        ############################################

        # now we run it in the engine
        try:
            # query = command.replace(";", "")
            if self.engine.tag == "Oracle":
                command = command.replace(";", "")
            # print([command])
            cur.execute(command)
            column_names = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            print("Real engine result:")
            print(column_names)
            for row in rows:
                print(row)
        except Exception as e:
            print("Error:", e)
            their_error = True
        self.conn.rollback()


        if their_error and our_error:
            assert our_error == their_error
        elif not their_error and not our_error:
            print("got ", len(rows), "vs", len(mytable.rows))
            compare_result = Engine().Compare(mytable.rows, rows, self.engine)
            if not compare_result:
                self.__class__.stats['compare_false'] += 1
                if test_index is not None:
                    self.__class__.error_ids['compare_false_ids'].append((current_test_id, test_index))
                    print(f"Compare returned False! Test index i={test_index}, Stats: {self.__class__.stats}")
                else:
                    self.__class__.error_ids['compare_false_ids'].append(current_test_id)
                    print(f"Compare returned False! Stats: {self.__class__.stats}")
            # else:
            #     self.__class__.stats['both_success'] += 1
            assert compare_result
        else:
            if our_error and not their_error:
                self.__class__.stats['our_error'] += 1
                if test_index is not None:
                    self.__class__.error_ids['our_error_ids'].append((current_test_id, test_index))
                    print(f"Our error only! Test index i={test_index}, Stats: {self.__class__.stats}")
                else:
                    self.__class__.error_ids['our_error_ids'].append(current_test_id)
                    print(f"Our error only! Stats: {self.__class__.stats}")
                print("our_error")
                print(our_error)
            if their_error and not our_error:
                self.__class__.stats['their_error'] += 1
                if test_index is not None:
                    self.__class__.error_ids['their_error_ids'].append((current_test_id, test_index))
                    print(f"Their error only! Test index i={test_index}, Stats: {self.__class__.stats}")
                else:
                    self.__class__.error_ids['their_error_ids'].append(current_test_id)
                    print(f"Their error only! Stats: {self.__class__.stats}")
                print("their_error")
                print(their_error)
            assert our_error == their_error



        ##############################################################################
        ##############################################################################
        # if not simplification and their_error and self.engine.tag == "Oracle":
        #     return
        #
        # if not simplification and their_error and self.engine.tag == "Postgres":
        #     return
        #
        # if not our_error and not their_error and self.engine.tag == "Oracle":
        #     print("got ", len(rows), "vs", len(mytable.rows))
        #     res = Engine().Compare(mytable.rows, rows, self.engine)
        #     assert res
        #
        # elif not our_error and not their_error and self.engine.tag == "Postgres":
        #     assert Engine().Compare(mytable.rows, rows, self.engine)
        #
        # elif not our_error:
        #     print("got ", len(rows), "vs", len(mytable.rows))
        #     assert Engine().Compare(mytable.rows, rows, self.engine) and (our_error == their_error)
        # else:
        #     print("our_error")
        #     print(our_error)
        #     print("their_error")
        #     print(their_error)
        #     assert our_error == their_error
        ##############################################################################
        ##############################################################################

        cur.close()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        print("\n" + "=" * 60)
        print("result:")
        print("=" * 60)
        print(f"we fail: {cls.stats['our_error']}")
        print(f"they fail: {cls.stats['their_error']}")
        print(f"Compare False: {cls.stats['compare_false']}")
        print("=" * 60)
        print(f"\nOur error list({len(cls.error_ids['our_error_ids'])}):")
        print(cls.error_ids['our_error_ids'])
        print(f"\ntheir error list({len(cls.error_ids['their_error_ids'])}):")
        print(cls.error_ids['their_error_ids'])
        print(f"\nCompare False list({len(cls.error_ids['compare_false_ids'])}):")
        print(cls.error_ids['compare_false_ids'])
        print("=" * 60)
