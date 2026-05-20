"""
JOIN Test Suite

Tests for [INNER] JOIN ON syntax support.
"""

import unittest
from interpreter.queryGenerator import *
from interpreter.Runtime import Eta
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.Database import Database
from interpreter.syntax.engine.Postgres import Postgres


class TestJoin(unittest.TestCase):
    """
    Tests for JOIN functionality in the SQL interpreter.
    Tests JOIN transformation to CROSS JOIN + WHERE.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test data and engine."""
        cls.engine = Postgres()
        cls.parser = Parser()
        cls.setup_test_data()
    
    @classmethod
    def setup_test_data(cls):
        """Create sample test data for JOIN tests."""
        # Sample data for TA table (name, height, age)
        rows_ta = [
            [BValue("Alice"), BValue(165.5), BValue(25)],
            [BValue("Bob"), BValue(180.0), BValue(30)],
            [BValue("Charlie"), BValue(175.0), BValue(25)],
        ]
        for row in rows_ta:
            for cell in row:
                cell.unknown = False
        
        # Sample data for TB table (realage, fullname, fullheight)
        rows_tb = [
            [BValue(25), BValue("Alice"), BValue(165.5)],
            [BValue(30), BValue("Bob"), BValue(180.0)],
            [BValue(25), BValue("Charlie"), BValue(175.0)],
        ]
        for row in rows_tb:
            for cell in row:
                cell.unknown = False
        
        # Sample data for TC table (newage, newheight, newname)
        rows_tc = [
            [BValue(25), BValue(165.5), BValue("Alice")],
            [BValue(30), BValue(180.0), BValue("Bob")],
        ]
        for row in rows_tc:
            for cell in row:
                cell.unknown = False
        
        cls.db = Database({
            "TA": Table(["name", "height", "age"], rows_ta),
            "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
            "TC": Table(["newage", "newheight", "newname"], rows_tc)
        })
        
        cls.dbt = {
            "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
            "TB": RelationType([NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
            "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
        }
    
    def parse_command(self, command):
        """Parse SQL command into query object."""
        parsed = sqlparse.parse(command)
        statement = parsed[0]
        query_object = self.parser.parse_select(statement)
        return query_object
    
    def execute_query(self, command: str):
        """
        Execute command in interpreter and return results.
        Returns tuple of (column_names, rows) or raises exception.
        """
        print(f"\n{'='*60}")
        print(f"Testing: {command}")
        print(f"{'='*60}")
        
        try:
            # Parse
            parsed = self.parse_command(command)
            print(f"Parsed: {parsed}")
            
            # Type check
            TQ = self.engine.typechecker.typecheck_query(self.dbt, RelationType([]), parsed)
            T = TQ[0]
            qp = TQ[1]
            print(f"Type checked: {T}")
            
            # Run query
            result_table = self.engine.run.run_query(self.db, Eta([], []), qp)
            
            # Extract results
            rows = [[cell.v for cell in row] for row in result_table.rows]
            cols = result_table.cols
            
            print(f"Result ({len(rows)} rows):")
            print(f"Columns: {cols}")
            for row in rows:
                print(f"  {row}")
            
            return cols, rows
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def assert_result(self, command: str, expected_rows):
        """Execute query and assert results match expected."""
        cols, actual_rows = self.execute_query(command)
        
        # Sort both for comparison (order might vary)
        actual_sorted = sorted([sorted(str(cell) for cell in row) for row in actual_rows])
        expected_sorted = sorted([sorted(str(cell) for cell in row) for row in expected_rows])
        
        self.assertEqual(actual_sorted, expected_sorted, 
                        f"Result mismatch!\nExpected: {expected_rows}\nActual: {actual_rows}")
        print("✓ Test passed!")
    
    # ==================== Basic JOIN Tests ====================
    
    def test_basic_join(self):
        """Test basic JOIN with ON condition."""
        # TA has Alice, Bob, Charlie
        # TB has Alice, Bob, Charlie
        # Should return 3 rows joining on name = fullname
        cols, rows = self.execute_query("SELECT * FROM TA JOIN TB ON TA.name = TB.fullname;")
        self.assertEqual(len(rows), 3)
        # Verify columns are from both tables (6 total: 3 from TA + 3 from TB)
        self.assertEqual(len(cols), 6)
    
    def test_inner_join(self):
        """Test INNER JOIN (equivalent to JOIN)."""
        # Should give same result as basic JOIN
        cols, rows = self.execute_query("SELECT * FROM TA INNER JOIN TB ON TA.name = TB.fullname;")
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(cols), 6)
    
    def test_join_with_projection(self):
        """Test JOIN with specific column selection."""
        cols, rows = self.execute_query("SELECT TA.name, TA.age, TB.realage FROM TA JOIN TB ON TA.name = TB.fullname;")
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(cols), 3)
    
    def test_join_with_where(self):
        """Test JOIN combined with WHERE clause."""
        # Filter to only age > 25
        cols, rows = self.execute_query("SELECT TA.name, TA.age FROM TA JOIN TB ON TA.name = TB.fullname WHERE TA.age > 25;")
        # Should return only Bob (age=30)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Bob")
    
    def test_multiple_joins(self):
        """Test multiple JOINs in sequence."""
        # TA -> TB -> TC
        # TA has Alice, Bob, Charlie
        # TB has Alice, Bob, Charlie  
        # TC has Alice, Bob (but not Charlie)
        # Should return 2 rows (Alice and Bob)
        cols, rows = self.execute_query(
            "SELECT TA.name FROM TA "
            "JOIN TB ON TA.name = TB.fullname "
            "JOIN TC ON TB.fullname = TC.newname;"
        )
        self.assertEqual(len(rows), 2)
        names = sorted([row[0] for row in rows])
        self.assertEqual(names, ["Alice", "Bob"])
    
    def test_join_with_aggregates(self):
        """Test JOIN with GROUP BY and aggregates."""
        cols, rows = self.execute_query(
            "SELECT TA.name, COUNT(*) AS cnt "
            "FROM TA JOIN TB ON TA.name = TB.fullname "
            "GROUP BY TA.name;"
        )
        self.assertEqual(len(rows), 3)
        # Each name appears once in the join
        for row in rows:
            self.assertEqual(row[1], 1)
    
    def test_join_equivalence_to_cross_where(self):
        """Test that JOIN ON is equivalent to CROSS JOIN with WHERE."""
        # These two should give the same result:
        # SELECT * FROM TA JOIN TB ON TA.name = TB.fullname
        # SELECT * FROM TA, TB WHERE TA.name = TB.fullname
        
        cols1, rows1 = self.execute_query("SELECT * FROM TA JOIN TB ON TA.name = TB.fullname;")
        cols2, rows2 = self.execute_query("SELECT * FROM TA, TB WHERE TA.name = TB.fullname;")
        
        # Same number of rows and columns
        self.assertEqual(len(rows1), len(rows2))
        self.assertEqual(len(cols1), len(cols2))


if __name__ == "__main__":
    unittest.main()
