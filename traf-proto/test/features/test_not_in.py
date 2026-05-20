"""Tests for NOT IN operator"""

import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from pathlib import Path
import unittest
from test.engines.engine_testing import TestEngine


class TestNotIn(TestEngine):
    """Test NOT IN operator implementation"""

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

    def test_not_in_simple(self):
        """Test NOT IN with simple subquery"""
        self.compare_command("""
            SELECT name FROM pilot 
            WHERE pilot_id NOT IN (SELECT winning_pilot FROM match WHERE country = 'Australia')
        """)

    def test_not_in_with_numbers(self):
        """Test NOT IN with numeric values"""
        self.compare_command("""
            SELECT name FROM TA 
            WHERE age NOT IN (SELECT realage FROM TB WHERE realage > 30)
        """)

    def test_not_in_empty_result(self):
        """Test NOT IN with subquery returning no rows"""
        self.compare_command("""
            SELECT name FROM TA 
            WHERE age NOT IN (SELECT realage FROM TB WHERE realage > 1000)
        """)

    def test_not_in_with_and(self):
        """Test NOT IN combined with AND condition"""
        self.compare_command("""
            SELECT name FROM TA 
            WHERE age NOT IN (SELECT realage FROM TB) AND height > 170
        """)

    def test_not_in_with_or(self):
        """Test NOT IN combined with OR condition"""
        self.compare_command("""
            SELECT name FROM TA 
            WHERE age NOT IN (SELECT realage FROM TB WHERE realage < 30) OR height < 160
        """)

    def test_not_in_comparison_with_in(self):
        """Test that NOT IN is the opposite of IN"""
        # This query should return names that are NOT winning pilots from Australia
        query1 = """
            SELECT name FROM pilot 
            WHERE pilot_id IN (SELECT winning_pilot FROM match WHERE country = 'Australia')
        """
        
        query2 = """
            SELECT name FROM pilot 
            WHERE pilot_id NOT IN (SELECT winning_pilot FROM match WHERE country = 'Australia')
        """
        
        self.compare_command(query1)
        self.compare_command(query2)


if __name__ == '__main__':
    unittest.main()
