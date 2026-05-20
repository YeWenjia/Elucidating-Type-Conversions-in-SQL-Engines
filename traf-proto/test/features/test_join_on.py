"""Tests for JOIN ... ON syntax"""

import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from pathlib import Path
import unittest
from test.engines.engine_testing import TestEngine


class TestJoinOn(TestEngine):
    """Test JOIN with ON clause"""

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

    def test_join_on_with_where(self):
        """Test JOIN with ON clause and WHERE condition (allergy_1/0046)"""
        self.compare_command("""
            SELECT stuid
            FROM has_allergy t1
            JOIN allergy_type t2 ON t1.allergy = t2.allergy
            WHERE t2.allergytype = 'food'
        """)

    def test_join_on_simple(self):
        """Test simple JOIN with ON clause"""
        self.compare_command("""
            SELECT TA.name, TB.fullname
            FROM TA
            JOIN TB ON TA.age = TB.realage
        """)

    def test_join_on_with_alias(self):
        """Test JOIN with ON clause using table aliases"""
        self.compare_command("""
            SELECT t1.name, t2.fullname
            FROM TA t1
            JOIN TB t2 ON t1.age = t2.realage
        """)

    def test_join_on_multiple_conditions(self):
        """Test JOIN with multiple ON conditions"""
        self.compare_command("""
            SELECT TA.name
            FROM TA
            JOIN TB ON TA.age = TB.realage AND TA.height > 160
        """)


if __name__ == '__main__':
    unittest.main()
