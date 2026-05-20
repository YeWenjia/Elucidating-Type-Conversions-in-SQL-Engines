from interpreter.Typechecker import *
from interpreter.queryGenerator import *
import unittest

from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.engine.Mysql import Mysql
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.syntax.engine.Mssql import Mssql
from interpreter.syntax.engine.Oracle import Oracle
from interpreter.syntax.type.RelationType import RelationType, NameType


class TestRuntime(unittest.TestCase):
    rows_ta = [[BValue("Lucas Davis"), BValue(6.0, False), BValue(31, False)],
               [BValue("John Doe"), BValue(5.8, False), BValue(30, False)],
               [BValue("Jane Smith"), BValue(-5.5, False), BValue(25, False)],
               [BValue("Michael Johnson"), BValue(6.2, False), BValue(35, False)],
               [BValue("David Wilson"), BValue(5.1, False), BValue(-32, False)]]
    rows_tb = [[BValue(-28, False), BValue("Emily Davis"), BValue(5.9, False)],
               [BValue(32, False), BValue("David Wilson"), BValue(5.1, False)],
               [BValue(27, False), BValue("Sarah Brown"), BValue(5.6, False)],
               [BValue(29, False), BValue("Matthew Lee"), BValue(5.2, False)],
               [BValue(32, False), BValue("Lucas Parker"), BValue(6.0, False)]]
    rows_tc = [[BValue(35, False), BValue(6.2, False), BValue("Michael Johnson")],
               [BValue(28, False), BValue(-5.9, False), BValue("Emily Davis")],
               [BValue(32, False), BValue(5.1, False), BValue("David Wilson")],
               [BValue(-32, False), BValue(6.0, False), BValue("Lucas Parker")],
               [BValue(27, False), BValue(5.6, False), BValue("Sarah Brown")]]
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

    # engine = Postgres()
    # engine = Mysql()
    engine = Sqlite()

    # engine = Mssql()
    # engine = Oracle()

    def run_command(self, command: str):
        print()
        parsed = sqlparse.parse(command, False)

        statement = parsed[0]
        q: Query = Parser(False).parse_select(statement)
        print("parsed", [q])
        TQ = self.engine.typechecker.typecheck_query(self.schema, q)
        T = TQ[0]
        qp = TQ[1]
        print("type is :", T)
        print("Translation result is: ", qp)
        our_res = self.engine.run.run_query(self.db, qp)
        print("Running result is: ", our_res)
        assert 1 == 1

    def test_simple_0(self):
        self.run_command("SELECT CAST(TC.newheight + TC.newheight AS INT) FROM TC TC")

    def test_debug(self):
        self.run_command("SELECT '0' AS col0 FROM TA TA WHERE TA.name < 'hlwen';")

    def test_bug_1(self):
        self.run_command("SELECT 0 AS col0 FROM TB TB WHERE TB.fullheight < TB.fullname;")

    def test_bug_2(self):
        self.run_command("SELECT 0 AS col0 FROM TA TA UNION SELECT 11.5 AS col0 FROM TA TA0,TC TC1;")

    def test_bug_3(self):
        self.run_command("SELECT TB1.fullname + TB1.fullheight AS col0 FROM TC TC0,TB TB1;")

    def test_bug_4(self):
        self.run_command("SELECT TB.realage + TB.fullheight AS col0 FROM TB TB;")

    def test_bug_5(self):
        self.run_command("SELECT CAST(TA0.name AS DECIMAL(10,1)) AS col0 FROM TA TA0,TB TB1;")

    def test_plus(self):
        self.run_command("SELECT 5.1 + 5.8 FROM TA")

    def test_plus_2(self):
        self.run_command(
            "SELECT TB.fullheight, TB.fullname, TB.fullheight + TB.fullname FROM TB TB WHERE TB.fullheight + TB.fullname < TB.fullheight")

    def test_wtf(self):
        self.run_command(
            "SELECT TA.age + TA.height AS col0 FROM TA TA EXCEPT SELECT TC.newheight + TC.newage AS col0 FROM TC TC;")
