#!/usr/bin/env python3
"""Test concat method for RelationType"""

from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.ValueType import SType, ZType, RType, BType

def test_concat_non_overlapping():
    """Test concat with non-overlapping columns"""
    print("\n" + "="*60)
    print("Test 1: Non-overlapping columns")
    print("="*60)
    
    t1 = RelationType([
        NameType("col1", ZType()),
        NameType("col2", SType())
    ])
    
    t2 = RelationType([
        NameType("col3", RType()),
        NameType("col4", BType())
    ])
    
    result = t1.concat(t2)
    print(f"T1: {t1}")
    print(f"T2: {t2}")
    print(f"T1.concat(T2): {result}")
    
    # Should have all 4 columns
    assert len(result.nametypes) == 4, f"Expected 4 columns, got {len(result.nametypes)}"
    assert result.nametypes[0].name == "col1"
    assert result.nametypes[1].name == "col2"
    assert result.nametypes[2].name == "col3"
    assert result.nametypes[3].name == "col4"
    print("✓ Non-overlapping concat works correctly")


def test_concat_overlapping():
    """Test concat with overlapping columns (replacement)"""
    print("\n" + "="*60)
    print("Test 2: Overlapping columns (replacement)")
    print("="*60)
    
    t1 = RelationType([
        NameType("col1", ZType()),
        NameType("col2", SType()),
        NameType("col3", ZType())
    ])
    
    t2 = RelationType([
        NameType("col2", RType()),  # This should replace col2 in t1
        NameType("col4", BType())
    ])
    
    result = t1.concat(t2)
    print(f"T1: {t1}")
    print(f"T2: {t2}")
    print(f"T1.concat(T2): {result}")
    
    # Should have 4 columns: col1, col2 (replaced), col3, col4
    assert len(result.nametypes) == 4, f"Expected 4 columns, got {len(result.nametypes)}"
    assert result.nametypes[0].name == "col1"
    assert isinstance(result.nametypes[0].type, ZType)
    
    assert result.nametypes[1].name == "col2"
    assert isinstance(result.nametypes[1].type, RType), f"col2 should be RType (replaced), got {type(result.nametypes[1].type)}"
    
    assert result.nametypes[2].name == "col3"
    assert isinstance(result.nametypes[2].type, ZType)
    
    assert result.nametypes[3].name == "col4"
    assert isinstance(result.nametypes[3].type, BType)
    
    print("✓ Overlapping concat with replacement works correctly")


def test_concat_empty():
    """Test concat with empty RelationType"""
    print("\n" + "="*60)
    print("Test 3: Concat with empty RelationType")
    print("="*60)
    
    t1 = RelationType([
        NameType("col1", ZType()),
        NameType("col2", SType())
    ])
    
    t_empty = RelationType([])
    
    # Concat empty to non-empty
    result1 = t1.concat(t_empty)
    print(f"T1.concat(empty): {result1}")
    assert len(result1.nametypes) == 2
    assert result1.nametypes[0].name == "col1"
    assert result1.nametypes[1].name == "col2"
    
    # Concat non-empty to empty
    result2 = t_empty.concat(t1)
    print(f"empty.concat(T1): {result2}")
    assert len(result2.nametypes) == 2
    assert result2.nametypes[0].name == "col1"
    assert result2.nametypes[1].name == "col2"
    
    # Concat empty to empty
    result3 = t_empty.concat(RelationType([]))
    print(f"empty.concat(empty): {result3}")
    assert len(result3.nametypes) == 0
    
    print("✓ Empty concat works correctly")


def test_concat_all_overlap():
    """Test concat where all columns overlap"""
    print("\n" + "="*60)
    print("Test 4: All columns overlap (complete replacement)")
    print("="*60)
    
    t1 = RelationType([
        NameType("col1", ZType()),
        NameType("col2", SType())
    ])
    
    t2 = RelationType([
        NameType("col1", RType()),  # Replace col1
        NameType("col2", BType())   # Replace col2
    ])
    
    result = t1.concat(t2)
    print(f"T1: {t1}")
    print(f"T2: {t2}")
    print(f"T1.concat(T2): {result}")
    
    # Should have 2 columns, both replaced
    assert len(result.nametypes) == 2, f"Expected 2 columns, got {len(result.nametypes)}"
    assert result.nametypes[0].name == "col1"
    assert isinstance(result.nametypes[0].type, RType), "col1 should be replaced with RType"
    
    assert result.nametypes[1].name == "col2"
    assert isinstance(result.nametypes[1].type, BType), "col2 should be replaced with BType"
    
    print("✓ Complete overlap with replacement works correctly")


def test_concat_qualified_names():
    """Test concat with qualified column names (table.column)"""
    print("\n" + "="*60)
    print("Test 5: Qualified column names")
    print("="*60)
    
    t1 = RelationType([
        NameType("TA.name", SType()),
        NameType("TA.age", ZType())
    ])
    
    t2 = RelationType([
        NameType("TB.fullname", SType()),
        NameType("TB.realage", ZType())
    ])
    
    result = t1.concat(t2)
    print(f"T1 (TA columns): {t1}")
    print(f"T2 (TB columns): {t2}")
    print(f"T1.concat(T2): {result}")
    
    # Should have all 4 columns
    assert len(result.nametypes) == 4
    assert result.nametypes[0].name == "TA.name"
    assert result.nametypes[1].name == "TA.age"
    assert result.nametypes[2].name == "TB.fullname"
    assert result.nametypes[3].name == "TB.realage"
    
    print("✓ Qualified names concat works correctly")


def test_concat_use_case():
    """Test the actual use case: combining outer scope with inner scope"""
    print("\n" + "="*60)
    print("Test 6: Correlated subquery use case")
    print("="*60)
    
    # Outer query scope: SELECT * FROM TA
    outer_scope = RelationType([
        NameType("TA.name", SType()),
        NameType("TA.height", RType()),
        NameType("TA.age", ZType())
    ])
    
    # Inner query scope: SELECT TB.fullname FROM TB
    inner_scope = RelationType([
        NameType("TB.realage", ZType()),
        NameType("TB.fullname", SType()),
        NameType("TB.fullheight", RType())
    ])
    
    # When typechecking the subquery, we need to combine scopes
    # so that references to TA.name are valid within the subquery
    combined = outer_scope.concat(inner_scope)
    
    print(f"Outer scope (TA): {outer_scope}")
    print(f"Inner scope (TB): {inner_scope}")
    print(f"Combined scope: {combined}")
    
    # Should have all 6 columns
    assert len(combined.nametypes) == 6
    
    # Verify we can find both TA and TB columns
    assert "TA.name" in [nt.name for nt in combined.nametypes]
    assert "TB.fullname" in [nt.name for nt in combined.nametypes]
    
    # Verify getTypeByName works for both
    ta_name_type = combined.getTypeByName("TA.name")
    assert isinstance(ta_name_type, SType)
    
    tb_fullname_type = combined.getTypeByName("TB.fullname")
    assert isinstance(tb_fullname_type, SType)
    
    print("✓ Correlated subquery use case works correctly")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing RelationType.concat() method")
    print("="*60)
    
    test_concat_non_overlapping()
    test_concat_overlapping()
    test_concat_empty()
    test_concat_all_overlap()
    test_concat_qualified_names()
    test_concat_use_case()
    
    print("\n" + "="*60)
    print("✓ All concat tests passed!")
    print("="*60)
    print("\nThe concat method is ready for use in Phase 3.")
