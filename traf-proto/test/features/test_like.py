"""
Tests for LIKE operator functionality
"""
import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from pathlib import Path
import unittest
from test.engines.engine_testing import TestEngine


class TestLike(TestEngine):
    """Test LIKE operator implementation"""

    @classmethod
    def setUpClass(cls):
        cls.engine = Postgres()
        cls.lark = True
        cls.parser = LarkParser()

        config_path = Path(__file__).parent.parent / "config.yml"

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

    def test_like_single_wildcard_end(self):
        """Test LIKE with % at the end"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE 'Alice%';")

    def test_like_single_wildcard_start(self):
        """Test LIKE with % at the start"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE '%ice';")

    def test_like_double_wildcard(self):
        """Test LIKE with % at both ends"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE '%li%';")

    def test_like_no_match(self):
        """Test LIKE with pattern that doesn't match"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE '%xyz%';")

    def test_like_exact_match(self):
        """Test LIKE with exact string (no wildcards)"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE 'Alice';")

    def test_like_underscore_wildcard(self):
        """Test LIKE with _ (single character wildcard)"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE 'Alic_';")

    def test_like_with_select_columns(self):
        """Test LIKE in WHERE with multiple SELECT columns"""
        self.compare_command("SELECT name, age FROM TA WHERE name LIKE '%a%';")

    def test_like_with_and(self):
        """Test LIKE combined with AND"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE '%a%' AND age > 20;")

    def test_like_with_or(self):
        """Test LIKE combined with OR"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE 'Alice%' OR age > 30;")

    def test_like_case_sensitive(self):
        """Test LIKE is case-sensitive by default"""
        self.compare_command("SELECT name FROM TA WHERE name LIKE '%ALICE%';")


if __name__ == '__main__':
    unittest.main()
