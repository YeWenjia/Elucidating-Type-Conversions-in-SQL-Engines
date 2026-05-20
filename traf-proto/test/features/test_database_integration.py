"""
Simple test to verify Database integration in tests.
Tests that Database works with existing test patterns.
"""

from interpreter.queryGenerator import *
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.Database import Database

def test_database_basic_operations():
    """Test basic database operations used in tests."""
    print("\n" + "="*60)
    print("Testing Database Integration")
    print("="*60)
    
    # Test 1: Initialize with empty database (like engine_testing.py)
    print("\n1. Testing empty database initialization...")
    db = Database({})
    assert len(db) == 0, "Empty database should have 0 tables"
    print("   ✓ Empty database initialization works")
    
    # Test 2: Initialize with tables (like test_lark.py, test_join.py, etc.)
    print("\n2. Testing database initialization with tables...")
    rows_ta = [
        [BValue("Alice"), BValue(165.5), BValue(25)],
        [BValue("Bob"), BValue(180.0), BValue(30)],
    ]
    for row in rows_ta:
        for cell in row:
            cell.unknown = False
    
    rows_tb = [
        [BValue(25), BValue("Alice"), BValue(165.5)],
        [BValue(30), BValue("Bob"), BValue(180.0)],
    ]
    for row in rows_tb:
        for cell in row:
            cell.unknown = False
    
    db = Database({
        "TA": Table(["name", "height", "age"], rows_ta),
        "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
    })
    
    assert len(db) == 2, "Database should have 2 tables"
    print("   ✓ Database initialization with tables works")
    
    # Test 3: Dictionary-style access (used throughout tests)
    print("\n3. Testing dictionary-style access...")
    ta_table = db["TA"]
    assert ta_table is not None, "Should retrieve TA table"
    assert ta_table.cols == ["name", "height", "age"], "Columns should match"
    print("   ✓ Dictionary-style access works")
    
    # Test 4: Adding tables dynamically (like populateDatabase in engine_testing.py)
    print("\n4. Testing dynamic table addition...")
    rows_tc = [
        [BValue(25), BValue(165.5), BValue("Alice")],
    ]
    for row in rows_tc:
        for cell in row:
            cell.unknown = False
    
    db["TC"] = Table(["newage", "newheight", "newname"], rows_tc)
    assert len(db) == 3, "Database should now have 3 tables"
    assert "TC" in db, "TC should be in database"
    print("   ✓ Dynamic table addition works")
    
    # Test 5: Iteration over database (used in some tests)
    print("\n5. Testing database iteration...")
    table_count = 0
    for table_name in db:
        table_count += 1
        assert table_name in ["TA", "TB", "TC"], f"Unexpected table: {table_name}"
    assert table_count == 3, "Should iterate over 3 tables"
    print("   ✓ Database iteration works")
    
    # Test 6: Check that Database behaves like dict for items()
    print("\n6. Testing items() iteration...")
    items_count = 0
    for name, table in db.items():
        items_count += 1
        assert isinstance(table, Table), "Value should be a Table"
    assert items_count == 3, "Should iterate over 3 items"
    print("   ✓ items() iteration works")
    
    # Test 7: Membership testing
    print("\n7. Testing membership ('in' operator)...")
    assert "TA" in db, "TA should be in database"
    assert "TB" in db, "TB should be in database"
    assert "TC" in db, "TC should be in database"
    assert "TD" not in db, "TD should not be in database"
    print("   ✓ Membership testing works")
    
    # Test 8: Case-insensitive lookup (Database feature)
    print("\n8. Testing case-insensitive lookup...")
    table_ta_lower = db.get_table("ta")
    assert table_ta_lower is not None, "Should find 'ta' (lowercase)"
    assert table_ta_lower.cols == ["name", "height", "age"], "Should return correct table"
    print("   ✓ Case-insensitive lookup works")
    
    print("\n" + "="*60)
    print("✓ All Database integration tests passed!")
    print("="*60)
    print("\nDatabase is fully compatible with test patterns.")
    print("Tests using Database instead of dict should work correctly.")

if __name__ == "__main__":
    test_database_basic_operations()
