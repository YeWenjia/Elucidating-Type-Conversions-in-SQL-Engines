"""
Test suite for Lark parser - verifies it generates compatible AST with sqlparse parser
"""

import unittest
from interpreter.lark_parser import LarkParser
from interpreter.queryGenerator import *
from interpreter.Runtime import Eta
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.Database import Database
from interpreter.syntax.engine.Postgres import Postgres


class TestLarkParser(unittest.TestCase):
    """Test Lark parser compatibility with existing interpreter"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data and engine."""
        cls.engine = Postgres()
        cls.parser = LarkParser()
        cls.setup_test_data()
    
    @classmethod
    def setup_test_data(cls):
        """Create sample test data."""
        rows_ta = [
            [BValue("Alice"), BValue(165.5), BValue(25)],
            [BValue("Bob"), BValue(180.0), BValue(30)],
            [BValue("Charlie"), BValue(175.0), BValue(25)],
            [BValue("Alice"), BValue(170.0), BValue(28)],
        ]
        for row in rows_ta:
            for cell in row:
                cell.unknown = False
        
        rows_tb = [
            [BValue(25), BValue("Alice"), BValue(165.5)],
            [BValue(30), BValue("Bob"), BValue(180.0)],
            [BValue(25), BValue("Charlie"), BValue(175.0)],
        ]
        for row in rows_tb:
            for cell in row:
                cell.unknown = False
        
        cls.db = Database({
            "TA": Table(["name", "height", "age"], rows_ta),
            "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
        })
        
        cls.dbt = {
            "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
            "TB": RelationType([NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
        }
    
    def execute_query(self, command: str):
        """Execute command and return results."""
        print(f"\n{'='*60}")
        print(f"Testing: {command}")
        print(f"{'='*60}")
        
        parsed = self.parser.parse(command)
        print(f"Parsed: {parsed}")
        
        TQ = self.engine.typechecker.typecheck_query(self.dbt, RelationType([]), parsed)
        T = TQ[0]
        qp = TQ[1]
        print(f"Type checked: {T}")
        
        result_table = self.engine.run.run_query(self.db, Eta([], []), qp)
        
        rows = [[cell.v for cell in row] for row in result_table.rows]
        cols = result_table.cols
        
        print(f"Result ({len(rows)} rows):")
        if len(rows) > 0:
            print(f"Columns: {cols}")
            for row in rows[:5]:
                print(f"  {row}")
        
        return cols, rows
    
    def test_select_star(self):
        """Test SELECT *"""
        cols, rows = self.execute_query("SELECT * FROM TA")
        self.assertEqual(cols, ["name", "height", "age"])
        self.assertEqual(len(rows), 4)
    
    def test_select_columns(self):
        """Test SELECT specific columns"""
        cols, rows = self.execute_query("SELECT name, age FROM TA")
        self.assertEqual(len(cols), 2)
        self.assertEqual(len(rows), 4)
    
    def test_where_clause(self):
        """Test WHERE filtering"""
        cols, rows = self.execute_query("SELECT name FROM TA WHERE age > 25")
        self.assertEqual(len(rows), 2)  # Bob (30) and Alice (28)
    
    def test_join(self):
        """Test JOIN with qualified names"""
        cols, rows = self.execute_query(
            "SELECT TA.name, TA.age, TB.realage FROM TA JOIN TB ON TA.name = TB.fullname"
        )
        self.assertEqual(len(rows), 4)  # Alice (2 matches), Bob, Charlie
    
    def test_join_with_where(self):
        """Test JOIN with additional WHERE clause"""
        cols, rows = self.execute_query(
            "SELECT TA.name FROM TA JOIN TB ON TA.name = TB.fullname WHERE TA.age = 25"
        )
        self.assertEqual(len(rows), 2)  # Alice (25) and Charlie (25)
    
    def test_group_by(self):
        """Test GROUP BY with COUNT"""
        cols, rows = self.execute_query(
            "SELECT name, COUNT(*) AS cnt FROM TA GROUP BY name"
        )
        self.assertEqual(len(rows), 3)  # Alice, Bob, Charlie
    
    def test_union(self):
        """Test UNION set operation"""
        cols, rows = self.execute_query(
            "SELECT name FROM TA UNION SELECT fullname FROM TB"
        )
        self.assertEqual(len(rows), 3)  # Alice, Bob, Charlie (deduplicated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
