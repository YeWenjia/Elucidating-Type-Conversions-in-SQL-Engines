"""
Aggregation Test Suite

Internal tests for GROUP BY, aggregate functions (COUNT, SUM, AVG, MAX, MIN), and HAVING clause.
Tests the interpreter in isolation without comparing to external databases.
"""

import unittest
from interpreter.queryGenerator import *
from interpreter.Runtime import Eta
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.Database import Database
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.lark_parser import LarkParser
from decimal import Decimal


class TestAggregation(unittest.TestCase):
    """
    Tests for aggregation functionality in the SQL interpreter.
    Tests run in isolation using sample data.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test data and engine."""
        cls.engine = Postgres()
        # Use LarkParser for GROUP BY/HAVING support
        cls.parser = LarkParser()
        cls.setup_test_data()
    
    @classmethod
    def setup_test_data(cls):
        """Create sample test data."""
        # Sample data for TA table (name, height, age)
        rows_ta = [
            [BValue("Alice"), BValue(165.5), BValue(25)],
            [BValue("Bob"), BValue(180.0), BValue(30)],
            [BValue("Charlie"), BValue(175.0), BValue(25)],
            [BValue("Alice"), BValue(165.5), BValue(28)],
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
        
        # Sample data for TD table - includes NULL values (name, score, grade)
        rows_td = [
            [BValue("Alice"), BValue(85), BValue("A")],
            [BValue("Bob"), Nullv(None), BValue("B")],      # NULL score
            [BValue("Charlie"), BValue(90), BValue("A")],
            [BValue("Dave"), Nullv(None), Nullv(None)],     # NULL score and grade
            [BValue("Eve"), BValue(75), BValue("C")],
        ]
        for row in rows_td:
            for cell in row:
                cell.unknown = False
        
        cls.db = Database({
            "TA": Table(["name", "height", "age"], rows_ta),
            "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
            "TC": Table(["newage", "newheight", "newname"], rows_tc),
            "TD": Table(["name", "score", "grade"], rows_td)
        })
        
        cls.dbt = {
            "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
            "TB": RelationType([NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
            "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())]),
            "TD": RelationType([NameType("name", SType()), NameType("score", ZType()), NameType("grade", SType())])
        }
    
    def parse_command(self, command):
        """Parse SQL command into query object."""
        query_object = self.parser.parse(command)
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
            
            # Type check
            TQ = self.engine.typechecker.typecheck_query(self.dbt, RelationType([]), parsed)
            T = TQ[0]
            qp = TQ[1]
            
            # Run query
            result_table = self.engine.run.run_query(self.db, Eta([], []), qp)
            rows = [[cell.erase() for cell in row] for row in result_table.rows]
            cols = result_table.cols
            
            print(f"Result ({len(rows)} rows):")
            print(f"Columns: {cols}")
            for row in rows:
                print(f"  {row}")
            
            return (cols, rows)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def assert_result(self, command: str, expected_rows, check_order=False):
        """
        Execute query and assert results match expected.
        
        Args:
            command: SQL query string
            expected_rows: List of expected result rows
            check_order: If True, check exact order; if False, sort before comparing
        """
        cols, actual_rows = self.execute_query(command)
        
        if not check_order:
            # Sort both for comparison (GROUP BY order may vary)
            expected_rows = sorted([tuple(r) for r in expected_rows])
            actual_rows = sorted([tuple(r) for r in actual_rows])
        
        self.assertEqual(len(actual_rows), len(expected_rows),
                        f"Row count mismatch: got {len(actual_rows)}, expected {len(expected_rows)}")
        
        for i, (actual, expected) in enumerate(zip(actual_rows, expected_rows)):
            self.assertEqual(actual, expected,
                           f"Row {i} mismatch:\n  Got:      {actual}\n  Expected: {expected}")
        
        print("✓ Test passed!")
        return True
    
    # ==================== COUNT Tests ====================
    
    def test_count_star_basic(self):
        """Test COUNT(*) without GROUP BY - should return single row with total count."""
        # TA has 4 rows
        self.assert_result(
            "SELECT COUNT(*) AS total FROM TA;",
            expected_rows=[[4]]
        )
    
    def test_count_with_group_by(self):
        """Test COUNT(*) with GROUP BY - existing test case."""
        # Alice appears 2 times, Bob 1 time, Charlie 1 time
        self.assert_result(
            "SELECT name AS col0, COUNT(*) AS col1 FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 2],
                ["Bob", 1],
                ["Charlie", 1]
            ]
        )
    
    def test_count_column(self):
        """Test COUNT(column) - excludes NULLs."""
        # All 4 rows have non-NULL names
        self.assert_result(
            "SELECT COUNT(name) AS cnt FROM TA;",
            expected_rows=[[4]]
        )
    
    def test_count_column_with_group_by(self):
        """Test COUNT(column) with GROUP BY."""
        self.assert_result(
            "SELECT name, COUNT(age) AS age_count FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 2],
                ["Bob", 1],
                ["Charlie", 1]
            ]
        )
    
    # ==================== COUNT(DISTINCT) Tests ====================
    
    def test_count_distinct_basic(self):
        """Test COUNT(DISTINCT column) without GROUP BY."""
        # TA has 3 distinct names: Alice, Bob, Charlie
        self.assert_result(
            "SELECT COUNT(DISTINCT name) AS distinct_names FROM TA;",
            expected_rows=[[3]]
        )
    
    def test_count_distinct_age(self):
        """Test COUNT(DISTINCT) on column with duplicate values."""
        # TA ages: 25, 30, 25, 28 -> 3 distinct values (25, 28, 30)
        self.assert_result(
            "SELECT COUNT(DISTINCT age) AS distinct_ages FROM TA;",
            expected_rows=[[3]]
        )
    
    def test_count_distinct_with_group_by(self):
        """Test COUNT(DISTINCT) with GROUP BY."""
        # For each name group, count distinct ages
        # Alice: [25, 28] -> 2 distinct
        # Bob: [30] -> 1 distinct
        # Charlie: [25] -> 1 distinct
        self.assert_result(
            "SELECT name, COUNT(DISTINCT age) AS distinct_ages FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 2],
                ["Bob", 1],
                ["Charlie", 1]
            ]
        )
    
    def test_count_distinct_all_same(self):
        """Test COUNT(DISTINCT) when all values are the same."""
        # TC has same newage for all rows (if setup that way)
        # For now, test with TA height where Alice has same height twice
        self.assert_result(
            "SELECT name, COUNT(DISTINCT height) AS distinct_heights FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 1],  # Both Alice rows have height 165.5
                ["Bob", 1],
                ["Charlie", 1]
            ]
        )
    
    def test_count_distinct_vs_count(self):
        """Test that COUNT(DISTINCT) differs from COUNT when there are duplicates."""
        # This query shows the difference
        # Alice has 2 rows but only 1 distinct height
        self.assert_result(
            "SELECT name, COUNT(height) AS total, COUNT(DISTINCT height) AS distinct_heights FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 2, 1],
                ["Bob", 1, 1],
                ["Charlie", 1, 1]
            ]
        )
    
    def test_count_distinct_empty_result(self):
        """Test COUNT(DISTINCT) on empty result set."""
        # No rows match the WHERE condition
        self.assert_result(
            "SELECT COUNT(DISTINCT name) AS cnt FROM TA WHERE age > 100;",
            expected_rows=[[0]]
        )
    
    # ==================== SUM Tests ====================
    
    def test_sum_basic(self):
        """Test SUM without GROUP BY."""
        # Ages: 25 + 30 + 25 + 28 = 108
        self.assert_result(
            "SELECT SUM(age) AS total_age FROM TA;",
            expected_rows=[[108]]
        )
    
    def test_sum_with_group_by(self):
        """Test SUM with GROUP BY."""
        # Alice: 25 + 28 = 53, Bob: 30, Charlie: 25
        self.assert_result(
            "SELECT name, SUM(age) AS total_age FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 53],
                ["Bob", 30],
                ["Charlie", 25]
            ]
        )
    
    def test_sum_integer_column(self):
        """Test SUM on integer column."""
        # TB realage: 25 + 30 + 25 = 80
        self.assert_result(
            "SELECT SUM(realage) AS sum_age FROM TB;",
            expected_rows=[[80]]
        )
    
    def test_sum_real_column(self):
        """Test SUM on real/decimal column."""
        # TA heights: 165.5 + 180.0 + 175.0 + 165.5 = 686.0
        self.assert_result(
            "SELECT SUM(height) AS sum_height FROM TA;",
            expected_rows=[[Decimal('686.0')]]
        )
    
    # ==================== AVG Tests ====================
    
    def test_avg_basic(self):
        """Test AVG without GROUP BY."""
        # Average age: (25 + 30 + 25 + 28) / 4 = 27
        self.assert_result(
            "SELECT AVG(age) AS avg_age FROM TA;",
            expected_rows=[[Decimal('27.0')]]
        )
    
    def test_avg_with_group_by(self):
        """Test AVG with GROUP BY."""
        # Alice: (25+28)/2 = 26.5, Bob: 30, Charlie: 25
        self.assert_result(
            "SELECT name, AVG(age) AS avg_age FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", Decimal('26.5')],
                ["Bob", Decimal('30.0')],
                ["Charlie", Decimal('25.0')]
            ]
        )
    
    def test_avg_real_column(self):
        """Test AVG on real column."""
        # Average height: (165.5 + 180.0 + 175.0 + 165.5) / 4 = 171.5
        self.assert_result(
            "SELECT AVG(height) AS avg_height FROM TA;",
            expected_rows=[[Decimal('171.5')]]
        )
    
    # ==================== MAX Tests ====================
    
    def test_max_basic(self):
        """Test MAX without GROUP BY."""
        # Max age: 30
        self.assert_result(
            "SELECT MAX(age) AS max_age FROM TA;",
            expected_rows=[[30]]
        )
    
    def test_max_with_group_by(self):
        """Test MAX with GROUP BY."""
        # Alice: max(25, 28) = 28, Bob: 30, Charlie: 25
        self.assert_result(
            "SELECT name, MAX(age) AS max_age FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 28],
                ["Bob", 30],
                ["Charlie", 25]
            ]
        )
    
    def test_max_string_column(self):
        """Test MAX on string column."""
        # Max name: "Charlie" (lexicographically)
        self.assert_result(
            "SELECT MAX(name) AS max_name FROM TA;",
            expected_rows=[["Charlie"]]
        )
    
    # ==================== MIN Tests ====================
    
    def test_min_basic(self):
        """Test MIN without GROUP BY."""
        # Min age: 25
        self.assert_result(
            "SELECT MIN(age) AS min_age FROM TA;",
            expected_rows=[[25]]
        )
    
    def test_min_with_group_by(self):
        """Test MIN with GROUP BY."""
        # Alice: min(25, 28) = 25, Bob: 30, Charlie: 25
        self.assert_result(
            "SELECT name, MIN(age) AS min_age FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 25],
                ["Bob", 30],
                ["Charlie", 25]
            ]
        )
    
    def test_min_string_column(self):
        """Test MIN on string column."""
        # Min name: "Alice" (lexicographically)
        self.assert_result(
            "SELECT MIN(name) AS min_name FROM TA;",
            expected_rows=[["Alice"]]
        )
    
    # ==================== Multiple Aggregates ====================
    
    def test_multiple_aggregates(self):
        """Test multiple aggregate functions in one query."""
        self.assert_result(
            "SELECT name, COUNT(*) AS cnt, SUM(age) AS sum_age, AVG(age) AS avg_age, "
            "MIN(age) AS min_age, MAX(age) AS max_age FROM TA GROUP BY name;",
            expected_rows=[
                ["Alice", 2, 53, Decimal('26.5'), 25, 28],
                ["Bob", 1, 30, Decimal('30.0'), 30, 30],
                ["Charlie", 1, 25, Decimal('25.0'), 25, 25]
            ]
        )
    
    def test_multiple_aggregates_no_group(self):
        """Test multiple aggregates without GROUP BY."""
        # Count: 4, Sum: 108, Avg: 27
        self.assert_result(
            "SELECT COUNT(*) AS cnt, SUM(age) AS sum_age, AVG(age) AS avg_age FROM TA;",
            expected_rows=[[4, 108, Decimal('27.0')]]
        )
    
    # ==================== Multiple Grouping Columns ====================
    
    def test_group_by_multiple_columns(self):
        """Test GROUP BY with multiple columns."""
        # Group by both name and age
        self.assert_result(
            "SELECT name, age, COUNT(*) AS cnt FROM TA GROUP BY name, age;",
            expected_rows=[
                ["Alice", 25, 1],
                ["Alice", 28, 1],
                ["Bob", 30, 1],
                ["Charlie", 25, 1]
            ]
        )
    
    def test_group_by_two_columns_with_aggregates(self):
        """Test GROUP BY two columns with multiple aggregates."""
        self.assert_result(
            "SELECT name, age, COUNT(*) AS cnt, SUM(height) AS sum_h FROM TA GROUP BY name, age;",
            expected_rows=[
                ["Alice", 25, 1, Decimal('165.5')],
                ["Alice", 28, 1, Decimal('165.5')],
                ["Bob", 30, 1, Decimal('180.0')],
                ["Charlie", 25, 1, Decimal('175.0')]
            ]
        )
    
    # ==================== WHERE with Aggregates ====================
    
    def test_where_before_group_by(self):
        """Test WHERE clause filters before GROUP BY."""
        # WHERE age > 25 filters to Bob(30), Alice(28)
        self.assert_result(
            "SELECT name, COUNT(*) AS cnt FROM TA WHERE age > 25 GROUP BY name;",
            expected_rows=[
                ["Alice", 1],  # Only the age=28 row
                ["Bob", 1]
            ]
        )
    
    def test_where_with_sum(self):
        """Test WHERE with SUM aggregate."""
        # WHERE age > 20 keeps all rows, same as no WHERE
        self.assert_result(
            "SELECT name, SUM(age) AS total FROM TA WHERE age > 20 GROUP BY name;",
            expected_rows=[
                ["Alice", 53],
                ["Bob", 30],
                ["Charlie", 25]
            ]
        )
    
    # ==================== HAVING Tests ====================
    
    def test_having_with_count(self):
        """Test HAVING with COUNT aggregate."""
        # Only Alice has COUNT(*) > 1
        self.assert_result(
            "SELECT name, COUNT(*) AS cnt FROM TA GROUP BY name HAVING COUNT(*) > 1;",
            expected_rows=[["Alice", 2]]
        )
    
    def test_having_with_sum(self):
        """Test HAVING with SUM aggregate."""
        # Alice: 53 > 50, Bob: 30 not > 50, Charlie: 25 not > 50
        self.assert_result(
            "SELECT name, SUM(age) AS total FROM TA GROUP BY name HAVING SUM(age) > 50;",
            expected_rows=[["Alice", 53]]
        )
    
    def test_having_with_avg(self):
        """Test HAVING with AVG aggregate."""
        # Bob: 30 > 27, Alice: 26.5 not > 27, Charlie: 25 not > 27
        self.assert_result(
            "SELECT name, AVG(age) AS avg_age FROM TA GROUP BY name HAVING AVG(age) > 27;",
            expected_rows=[["Bob", Decimal('30.0')]]
        )
    
    def test_having_on_grouping_column(self):
        """Test HAVING filtering on grouping column."""
        # 'Bob' > 'M' and 'Charlie' > 'M', but not 'Alice'
        self.assert_result(
            "SELECT name, COUNT(*) AS cnt FROM TA GROUP BY name HAVING name > 'B';",
            expected_rows=[
                ["Bob", 1],
                ["Charlie", 1]
            ]
        )
    
    def test_where_and_having(self):
        """Test WHERE and HAVING together."""
        # WHERE age > 20: all pass
        # GROUP BY name gives Alice:53, Bob:30, Charlie:25  
        # HAVING SUM(age) > 40: Alice:53
        self.assert_result(
            "SELECT name, SUM(age) AS total FROM TA WHERE age > 20 "
            "GROUP BY name HAVING SUM(age) > 40;",
            expected_rows=[["Alice", 53]]
        )
    
    # ==================== Edge Cases ====================
    
    def test_empty_result_group_by(self):
        """Test GROUP BY on empty result set."""
        # WHERE filters out all rows
        self.assert_result(
            "SELECT name, COUNT(*) AS cnt FROM TA WHERE age > 1000 GROUP BY name;",
            expected_rows=[]
        )
    
    def test_group_by_no_select_grouping_column(self):
        """Test GROUP BY without selecting the grouping column."""
        # Grouped by name but don't select it - should get one row per group (3 groups)
        # Cannot predict exact aggregates without knowing order, but can count rows
        cols, rows = self.execute_query("SELECT COUNT(*) AS cnt, SUM(age) AS total FROM TA GROUP BY name;")
        self.assertEqual(len(rows), 3, "Should have 3 groups (Alice, Bob, Charlie)")
        # Verify one row has cnt=2 (Alice) and two rows have cnt=1 (Bob, Charlie)
        counts = sorted([row[0] for row in rows])
        self.assertEqual(counts, [1, 1, 2])
    
    # ==================== HAVING Without SELECT Tests ====================
    
    def test_having_aggregate_not_in_select(self):
        """Test HAVING with aggregate not in SELECT clause."""
        # Only Alice has COUNT(*) > 1, but we only select name
        self.assert_result(
            "SELECT name FROM TA GROUP BY name HAVING COUNT(*) > 1;",
            expected_rows=[["Alice"]]
        )
    
    def test_having_sum_not_in_select(self):
        """Test HAVING with SUM not in SELECT clause."""
        # Alice: SUM(age)=53 > 50, but we only select name
        self.assert_result(
            "SELECT name FROM TA GROUP BY name HAVING SUM(age) > 50;",
            expected_rows=[["Alice"]]
        )
    
    def test_having_multiple_aggregates_partial_select(self):
        """Test HAVING with multiple aggregates, only some in SELECT."""
        # SELECT includes COUNT but not SUM
        # Alice has COUNT(*) > 1 AND SUM(age) > 50
        self.assert_result(
            "SELECT name, COUNT(*) AS cnt FROM TA GROUP BY name HAVING COUNT(*) > 1 AND SUM(age) > 50;",
            expected_rows=[["Alice", 2]]
        )
    
    def test_having_complex_expression_not_in_select(self):
        """Test HAVING with complex aggregate expression not in SELECT."""
        # HAVING uses AVG which is not in SELECT
        # Bob: AVG(age)=30 > 27
        self.assert_result(
            "SELECT name FROM TA GROUP BY name HAVING AVG(age) > 27;",
            expected_rows=[["Bob"]]
        )
    
    # ==================== NULL Handling Tests ====================
    
    def test_count_star_with_nulls(self):
        """Test COUNT(*) includes rows with NULL values."""
        # All 5 rows should be counted, even those with NULLs
        self.assert_result(
            "SELECT COUNT(*) AS cnt FROM TD;",
            expected_rows=[[5]]
        )
    
    def test_count_column_excludes_nulls(self):
        """Test COUNT(column) excludes NULL values."""
        # TD has 5 rows, but 2 have NULL score (Bob and Dave)
        self.assert_result(
            "SELECT COUNT(score) AS cnt FROM TD;",
            expected_rows=[[3]]
        )
    
    def test_sum_ignores_nulls(self):
        """Test SUM ignores NULL values."""
        # Scores: Alice=85, Bob=NULL, Charlie=90, Dave=NULL, Eve=75
        # SUM = 85 + 90 + 75 = 250
        self.assert_result(
            "SELECT SUM(score) AS total FROM TD;",
            expected_rows=[[250]]
        )
    
    def test_avg_ignores_nulls(self):
        """Test AVG ignores NULL values."""
        # Scores: 85, 90, 75 (excluding NULLs)
        # AVG = 250/3 = 83.333...
        cols, rows = self.execute_query("SELECT AVG(score) AS avg_score FROM TD;")
        self.assertEqual(len(rows), 1)
        # Check that result is approximately 83.33
        avg_val = float(rows[0][0])
        self.assertAlmostEqual(avg_val, 83.333333, places=5)
    
    def test_max_ignores_nulls(self):
        """Test MAX ignores NULL values."""
        # Max score = 90 (Charlie)
        self.assert_result(
            "SELECT MAX(score) AS max_score FROM TD;",
            expected_rows=[[90]]
        )
    
    def test_min_ignores_nulls(self):
        """Test MIN ignores NULL values."""
        # Min score = 75 (Eve)
        self.assert_result(
            "SELECT MIN(score) AS min_score FROM TD;",
            expected_rows=[[75]]
        )
    
    def test_group_by_with_nulls(self):
        """Test GROUP BY with NULL values in aggregated column."""
        # Group by grade: A has 2 rows (85+90=175), B has 1 row (NULL ignored), C has 1 row (75), NULL has 1 row (NULL ignored)
        cols, rows = self.execute_query("SELECT grade, SUM(score) AS total FROM TD GROUP BY grade;")
        self.assertEqual(len(rows), 4)  # 4 groups: A, B, C, NULL
        
        # Find the results
        results = {str(row[0]): row[1] for row in rows}
        self.assertEqual(results.get('A'), 175)
        self.assertEqual(results.get('C'), 75)
        # B group has only NULL score, so SUM should be NULL
        self.assertIsNone(results.get('B'))
    
    def test_all_nulls_returns_null(self):
        """Test aggregate on all-NULL column returns NULL."""
        # Create query that filters to only rows with NULL scores
        cols, rows = self.execute_query("SELECT SUM(score) AS total FROM TD WHERE name = 'Bob' OR name = 'Dave';")
        self.assertEqual(len(rows), 1)
        # Both Bob and Dave have NULL scores, so SUM should return NULL
        self.assertIsNone(rows[0][0])
    
    # ==================== Nested Aggregate Tests ====================
    
    def test_nested_aggregate_sum_count(self):
        """Test that nested aggregates like SUM(COUNT(*)) are rejected."""
        with self.assertRaises(Exception) as context:
            self.execute_query("SELECT SUM(COUNT(*)) FROM TA GROUP BY name;")
        self.assertIn("Nested aggregate", str(context.exception))
    
    def test_nested_aggregate_avg_sum(self):
        """Test that nested aggregates like AVG(SUM(age)) are rejected."""
        with self.assertRaises(Exception) as context:
            self.execute_query("SELECT AVG(SUM(age)) FROM TA GROUP BY name;")
        self.assertIn("Nested aggregate", str(context.exception))
    
    def test_nested_aggregate_max_count(self):
        """Test that nested aggregates like MAX(COUNT(*)) are rejected."""
        with self.assertRaises(Exception) as context:
            self.execute_query("SELECT MAX(COUNT(*)) FROM TA GROUP BY name;")
        self.assertIn("Nested aggregate", str(context.exception))
    
    def test_nested_aggregate_count_avg(self):
        """Test that nested aggregates like COUNT(AVG(age)) are rejected."""
        with self.assertRaises(Exception) as context:
            self.execute_query("SELECT COUNT(AVG(age)) FROM TA GROUP BY name;")
        self.assertIn("Nested aggregate", str(context.exception))


if __name__ == "__main__":
    unittest.main()
