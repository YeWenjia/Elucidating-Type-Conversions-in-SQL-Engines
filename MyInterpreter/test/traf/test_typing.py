from interpreter.Typechecker import *
from interpreter.queryGenerator import *
import unittest

from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.type.RelationType import RelationType, NameType


class TestTyping(unittest.TestCase):
    rows_ta = [[BValue("Lucas Davis"), BValue(6.0), BValue(31)], [BValue("John Doe"), BValue(5.8), BValue(30)],
               [BValue("Jane Smith"), BValue(-5.5), BValue(25)], [BValue("Michael Johnson"), BValue(6.2), BValue(35)],
               [BValue("David Wilson"), BValue(5.1), BValue(-32)]]
    rows_tb = [[BValue(-28), BValue("Emily Davis"), BValue(5.9)], [BValue(32), BValue("David Wilson"), BValue(5.1)],
               [BValue(27), BValue("Sarah Brown"), BValue(5.6)], [BValue(29), BValue("Matthew Lee"), BValue(5.2)],
               [BValue(32), BValue("Lucas Parker"), BValue(6.0)]]
    rows_tc = [[BValue(35), BValue(6.2), BValue("Michael Johnson")], [BValue(28), BValue(-5.9), BValue("Emily Davis")],
               [BValue(32), BValue(5.1), BValue("David Wilson")], [BValue(-32), BValue(6.0), BValue("Lucas Parker")],
               [BValue(27), BValue(5.6), BValue("Sarah Brown")]]
    db = {
        "TA": Table(["name", "height", "age"], rows_ta),
        "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
        "TC": Table(["newage", "newheight", "newname"], rows_tc)
    }

    schema = {
        "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
        "TB": RelationType(
            [NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
        "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
    }

    engine = Postgres()

    def run_command(self, command: str):
        parsed = sqlparse.parse(command)
        statement = parsed[0]
        q: Query = parse_select(statement)
        print("")
        TQ = self.engine.typechecker.typecheck_query(self.schema, q)
        T = TQ[0]
        qp = TQ[1]
        print("type is :", T)
        print("Translation result is: ", qp)
        assert 1 == 1

    def test_simple_0(self):
        self.run_command("SELECT name FROM TA")

    def test_simple(self):
        self.run_command("SELECT name, height, age+1, 'foo' FROM TA")

    def test_inter(self):
        self.run_command("SELECT name,age FROM TA INTERSECT SELECT name,age FROM TA")

    def test_inter2(self):
        self.run_command("SELECT 1,age FROM TA INTERSECT SELECT 2,age FROM TA")

    def test_inter3(self):
        self.run_command("SELECT '1',age FROM TA INTERSECT SELECT 2,'2' FROM TA")

    def test_sel(self):
        self.run_command("SELECT name FROM TA WHERE '1.5' < 2.1")

    def test_sel2(self):
        self.run_command("SELECT name FROM TA WHERE ('1.5' < 2.1 AND 1 = 2)")

    def test_asc(self):
        self.run_command("SELECT CAST('1' AS INT) FROM TA WHERE ('1.5' < 2.1 AND 1 = 2)")

    def test_asc_1(self):
        self.run_command("SELECT CAST('1' AS INT) FROM TA WHERE '1.5' < 2.1")

    def test_asc_2(self):
        self.run_command("SELECT CAST('1' AS INT) FROM TA WHERE ('1.5' < 2.1 AND '1' = 1)")

    def test_nested_asc(self):
        self.run_command("SELECT CAST(CAST('1' AS INT) AS DECIMAL(10,1)) FROM TA")

    def test_implicit_error_1(self):
        with self.assertRaises(TypeError):
            self.run_command("SELECT name + 1 FROM TA")
        with self.assertRaises(TypeError):
            self.run_command("SELECT 'name' + 1 FROM TA")

    def test_non_unique_names(self):
        with self.assertRaises(DuplicateNameError):
            self.run_command("SELECT name, name FROM TA")
