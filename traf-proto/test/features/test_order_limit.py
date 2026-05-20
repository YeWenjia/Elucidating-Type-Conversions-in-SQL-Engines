"""
Tests for ORDER BY and LIMIT functionality
"""
import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from pathlib import Path
import unittest
from test.engines.engine_testing import TestEngine


class TestOrderByLimit(TestEngine):
    """Test ORDER BY and LIMIT implementation"""

    @classmethod
    def setUpClass(cls):
        cls.engine = Postgres()
        cls.lark = True
        cls.parser = LarkParser()

        config_path = Path(__file__).parent.parent / "engines" / "newconfig.yml"

        with open(config_path, "r") as f:
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

    # ==================== ORDER BY Tests ====================
    
    def test_order_by_asc_single_column(self):
        """Test ORDER BY with single column ascending"""
        self.compare_command("SELECT name, age FROM TA ORDER BY age ASC;")

    def test_order_by_desc_single_column(self):
        """Test ORDER BY with single column descending"""
        self.compare_command("SELECT name, age FROM TA ORDER BY age DESC;")

    def test_order_by_implicit_asc(self):
        """Test ORDER BY without explicit ASC (default ascending)"""
        self.compare_command("SELECT name, age FROM TA ORDER BY age;")

    def test_order_by_multiple_columns(self):
        """Test ORDER BY with multiple columns"""
        self.compare_command("SELECT name, age, height FROM TA ORDER BY age ASC, height DESC;")

    def test_order_by_with_where(self):
        """Test ORDER BY combined with WHERE clause"""
        self.compare_command("SELECT name, age FROM TA WHERE age > 25 ORDER BY age DESC;")

    def test_order_by_string_column(self):
        """Test ORDER BY on string column"""
        self.compare_command("SELECT name, age FROM TA ORDER BY name ASC;")

    def test_order_by_with_join(self):
        """Test ORDER BY with JOIN"""
        self.compare_command("SELECT TA.name, TB.name FROM TA JOIN TB ON TA.age = TB.age ORDER BY TA.name;")

    def test_order_by_with_distinct(self):
        """Test ORDER BY combined with DISTINCT"""
        self.compare_command("SELECT DISTINCT age FROM TA ORDER BY age DESC;")

    def test_order_by_expression(self):
        """Test ORDER BY with expression"""
        self.compare_command("SELECT name, age, age + 10 AS age_plus FROM TA ORDER BY age + 10;")

    def test_order_by_qualified_name(self):
        """Test ORDER BY with table-qualified column name"""
        self.compare_command("SELECT TA.name, TA.age FROM TA ORDER BY TA.age;")

    def test_order_by_column_not_in_select(self):
        """Test ORDER BY with column not in SELECT clause (Spider pattern)"""
        # This should work: ORDER BY can reference columns not in SELECT
        self.compare_command("SELECT name FROM TA ORDER BY age DESC;")

    def test_order_by_multiple_columns_partial_select(self):
        """Test ORDER BY with multiple columns, only some in SELECT"""
        self.compare_command("SELECT name FROM TA ORDER BY age DESC, height ASC;")

    # ==================== LIMIT Tests ====================
    
    def test_limit_simple(self):
        """Test simple LIMIT clause"""
        self.compare_command("SELECT name, age FROM TA LIMIT 3;")

    def test_limit_with_order_by(self):
        """Test LIMIT combined with ORDER BY"""
        self.compare_command("SELECT name, age FROM TA ORDER BY age DESC LIMIT 2;")

    def test_limit_one(self):
        """Test LIMIT 1 (common for getting top result)"""
        self.compare_command("SELECT name, age FROM TA ORDER BY age DESC LIMIT 1;")

    def test_limit_zero(self):
        """Test LIMIT 0 (should return empty result)"""
        self.compare_command("SELECT name, age FROM TA LIMIT 0;")

    def test_limit_larger_than_result(self):
        """Test LIMIT larger than result set"""
        self.compare_command("SELECT name FROM TA LIMIT 1000;")

    # ==================== OFFSET Tests ====================
    
    def test_limit_with_offset(self):
        """Test LIMIT with OFFSET"""
        self.compare_command("SELECT name, age FROM TA ORDER BY age LIMIT 2 OFFSET 1;")

    def test_offset_only_limit(self):
        """Test OFFSET with small LIMIT"""
        self.compare_command("SELECT name, age FROM TA ORDER BY age LIMIT 1 OFFSET 2;")

    def test_offset_larger_than_result(self):
        """Test OFFSET larger than result set (should return empty)"""
        self.compare_command("SELECT name, age FROM TA LIMIT 5 OFFSET 100;")

    # ==================== Combined Complex Tests ====================
    
    def test_order_limit_where_combined(self):
        """Test WHERE + ORDER BY + LIMIT together"""
        self.compare_command("SELECT name, age FROM TA WHERE age > 20 ORDER BY age DESC LIMIT 2;")

    def test_order_limit_join_combined(self):
        """Test JOIN + ORDER BY + LIMIT"""
        self.compare_command(
            "SELECT TA.name, TB.name, TA.age FROM TA JOIN TB ON TA.age = TB.age "
            "ORDER BY TA.age DESC LIMIT 3;"
        )

    def test_order_limit_distinct_combined(self):
        """Test DISTINCT + ORDER BY + LIMIT"""
        self.compare_command("SELECT DISTINCT age FROM TA ORDER BY age ASC LIMIT 2;")

    # ==================== GROUP BY with ORDER BY Tests ====================
    # Note: These require aggregate support in ORDER BY
    
    def test_group_by_order_by_count(self):
        """Test GROUP BY with ORDER BY on aggregate function"""
        self.compare_command("SELECT age, COUNT(*) as cnt FROM TA GROUP BY age ORDER BY COUNT(*) DESC;")

    def test_group_by_order_by_hidden_aggregate(self):
        """Test GROUP BY with ORDER BY on aggregate NOT in SELECT (Spider pattern)"""
        # This is the challenging case from Spider tests
        self.compare_command("SELECT age FROM TA GROUP BY age ORDER BY COUNT(*) DESC;")

    def test_group_by_order_by_limit(self):
        """Test GROUP BY + ORDER BY + LIMIT (Spider pattern)"""
        self.compare_command("SELECT age FROM TA GROUP BY age ORDER BY COUNT(*) DESC LIMIT 1;")

    def test_group_by_multiple_order(self):
        """Test GROUP BY with ORDER BY on multiple columns"""
        self.compare_command(
            "SELECT age, COUNT(*) as cnt FROM TA GROUP BY age "
            "ORDER BY COUNT(*) DESC, age ASC LIMIT 3;"
        )

    # ==================== NULL Handling Tests ====================
    # Note: These tests assume TC table may have NULL values or test with existing data
    
    def test_order_by_nullable_column(self):
        """Test ORDER BY on a column that might contain NULLs"""
        # TC table has nullable 'value' column
        self.compare_command("SELECT name, value FROM TC ORDER BY value ASC;")

    def test_order_by_nullable_desc(self):
        """Test ORDER BY DESC on nullable column"""
        self.compare_command("SELECT name, value FROM TC ORDER BY value DESC;")

    # ==================== Edge Cases ====================
    
    def test_order_by_same_values(self):
        """Test ORDER BY when many rows have same value (stable sort)"""
        self.compare_command("SELECT name, age FROM TA WHERE age = 30 ORDER BY age;")

    def test_multiple_order_by_directions(self):
        """Test ORDER BY with mixed ASC/DESC on multiple columns"""
        self.compare_command("SELECT name, age, height FROM TA ORDER BY age ASC, height DESC, name ASC;")


if __name__ == '__main__':
    unittest.main()
