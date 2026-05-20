"""Tests for scalar subquery with = operator"""

import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from pathlib import Path
import unittest
from test.engines.engine_testing import TestEngine


class TestScalarSubquery(TestEngine):
    """Test scalar subqueries in comparisons"""

    @classmethod
    def setUpClass(cls):
        cls.engine = Postgres()
        cls.lark = True

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
        
        # Create parser with inferred schema after database is populated
        cls.parser = LarkParser(schema=cls.dbt)

    def test_scalar_subquery_with_min(self):
        """Test scalar subquery with MIN aggregate"""
        self.compare_command("""
            SELECT name
            FROM TA
            WHERE age = (SELECT MIN(age) FROM TA)
        """)

    def test_scalar_subquery_with_max(self):
        """Test scalar subquery with MAX aggregate"""
        self.compare_command("""
            SELECT name
            FROM TA
            WHERE height = (SELECT MAX(height) FROM TA)
        """)

    def test_scalar_subquery_comparison(self):
        """Test scalar subquery with greater than comparison"""
        self.compare_command("""
            SELECT name
            FROM TA
            WHERE age > (SELECT AVG(age) FROM TA)
        """)


if __name__ == '__main__':
    unittest.main()
