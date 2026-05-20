"""
Test cases for JOIN queries with table aliases to debug parsing issues.
"""

import pytest
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.ValueType import SType, ZType


class TestJoinWithAliases:
    """Test JOIN queries with table aliases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a minimal schema for testing
        faculty_schema = RelationType([
            NameType('facid', ZType()),
            NameType('lname', SType()),
            NameType('fname', SType()),
            NameType('rank', SType()),
            NameType('sex', SType()),
            NameType('phone', ZType()),
            NameType('room', SType()),
            NameType('building', SType())
        ])
        
        student_schema = RelationType([
            NameType('stuid', ZType()),
            NameType('lname', SType()),
            NameType('fname', SType()),
            NameType('age', ZType()),
            NameType('sex', SType()),
            NameType('major', ZType()),
            NameType('advisor', ZType()),
            NameType('city_code', SType())
        ])
        
        schema = {
            'faculty': faculty_schema,
            'student': student_schema
        }
        
        self.parser = LarkParser(schema=schema)
    
    def test_simple_table_alias(self):
        """Test simple SELECT with table alias."""
        sql = "SELECT T1.fname FROM faculty T1"
        try:
            result = self.parser.parse(sql)
            print(f"✓ Parsed: {result}")
            assert result is not None
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
            pytest.fail(f"Failed to parse simple alias: {e}")
    
    def test_join_without_alias(self):
        """Test JOIN without table aliases."""
        sql = "SELECT faculty.fname FROM faculty JOIN student ON faculty.facid = student.advisor"
        try:
            result = self.parser.parse(sql)
            print(f"✓ Parsed: {result}")
            assert result is not None
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
            pytest.fail(f"Failed to parse JOIN without alias: {e}")
    
    def test_join_with_one_alias(self):
        """Test JOIN with one table alias."""
        sql = "SELECT T1.fname FROM faculty T1 JOIN student ON T1.facid = student.advisor"
        try:
            result = self.parser.parse(sql)
            print(f"✓ Parsed: {result}")
            assert result is not None
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
            pytest.fail(f"Failed to parse JOIN with one alias: {e}")
    
    def test_join_with_both_aliases(self):
        """Test JOIN with both table aliases."""
        sql = "SELECT T1.fname FROM faculty T1 JOIN student T2 ON T1.facid = T2.advisor"
        try:
            result = self.parser.parse(sql)
            print(f"✓ Parsed: {result}")
            assert result is not None
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
            pytest.fail(f"Failed to parse JOIN with both aliases: {e}")
    
    def test_join_with_aliases_and_where(self):
        """Test JOIN with aliases and WHERE clause."""
        sql = "SELECT T1.fname FROM faculty T1 JOIN student T2 ON T1.facid = T2.advisor WHERE T2.fname = 'Linda'"
        try:
            result = self.parser.parse(sql)
            print(f"✓ Parsed: {result}")
            assert result is not None
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
            pytest.fail(f"Failed to parse JOIN with aliases and WHERE: {e}")
    
    def test_join_with_aliases_and_complex_where(self):
        """Test the actual failing query from 0018.yaml"""
        sql = "SELECT T1.fname, T1.lname FROM faculty T1 JOIN student T2 ON T1.facid = T2.advisor WHERE T2.fname = 'Linda' AND T2.lname = 'Smith'"
        try:
            result = self.parser.parse(sql)
            print(f"✓ Parsed: {result}")
            print(f"  Query structure: {result}")
            assert result is not None
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"Failed to parse full query from 0018.yaml: {e}")
    
    def test_join_alias_variations(self):
        """Test various alias naming patterns."""
        test_cases = [
            ("SELECT a.fname FROM faculty a", "single letter alias"),
            ("SELECT t1.fname FROM faculty t1", "lowercase t1"),
            ("SELECT T1.fname FROM faculty T1", "uppercase T1"),
            ("SELECT tbl.fname FROM faculty tbl", "word alias"),
        ]
        
        for sql, description in test_cases:
            try:
                result = self.parser.parse(sql)
                print(f"✓ {description}: {result}")
            except Exception as e:
                print(f"✗ {description} failed: {e}")
                pytest.fail(f"Failed {description}: {e}")


if __name__ == "__main__":
    # Run the tests with verbose output
    pytest.main([__file__, "-v", "-s"])
