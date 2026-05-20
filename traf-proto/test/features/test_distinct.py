"""
Tests for DISTINCT functionality
"""
import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from pathlib import Path
import unittest
from test.engines.engine_testing import TestEngine


class TestDistinct(TestEngine):
    """Test DISTINCT keyword implementation"""

    @classmethod
    def setUpClass(cls):
        cls.engine = Postgres()
        cls.lark = True
        cls.parser = LarkParser()

        config_path = Path(__file__).parent / "newconfig.yml"

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

    def test_distinct_simple(self):
        """Test simple DISTINCT on single column"""
        self.compare_command("SELECT DISTINCT name FROM TA;")

    def test_distinct_multiple_cols(self):
        """Test DISTINCT with multiple columns"""
        self.compare_command("SELECT DISTINCT name, age FROM TA;")

    def test_distinct_with_where(self):
        """Test DISTINCT with WHERE clause"""
        self.compare_command("SELECT DISTINCT name FROM TA WHERE age > 25;")

    def test_distinct_with_expression(self):
        """Test DISTINCT with expressions"""
        self.compare_command("SELECT DISTINCT age + 1 AS age_plus FROM TA;")

    def test_distinct_all_columns(self):
        """Test DISTINCT on all columns"""
        self.compare_command("SELECT DISTINCT name, height, age FROM TA;")

    def test_distinct_with_cast(self):
        """Test DISTINCT with CAST expression"""
        self.compare_command("SELECT DISTINCT CAST(height AS INT) AS h FROM TA;")

    def test_distinct_subquery(self):
        """Test DISTINCT in subquery"""
        self.compare_command("SELECT * FROM (SELECT DISTINCT name FROM TA) Sub1;")


if __name__ == '__main__':
    unittest.main()
