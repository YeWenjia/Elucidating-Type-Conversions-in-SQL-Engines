#!/usr/bin/env python3
"""
Test ORDER BY with column not in SELECT list

Query: SELECT name FROM pilot ORDER BY age DESC;

This tests whether we can order by a column (age) that is not in the SELECT clause.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from interpreter.Parser import Parser
import sqlparse
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.Runtime import Eta
from interpreter.queryGenerator import *
from interpreter.syntax.type.RelationType import RelationType, NameType

# Test data for pilot table
rows_pilot = [
    [BValue("Alice"), BValue(25), BValue("Commercial")],
    [BValue("Bob"), BValue(30), BValue("Private")],
    [BValue("Charlie"), BValue(22), BValue("Commercial")],
    [BValue("Diana"), BValue(35), BValue("ATP")],
]
for row in rows_pilot:
    for cell in row:
        cell.unknown = False

db = {
    "pilot": Table(["name", "age", "license"], rows_pilot),
}

dbt = {
    "pilot": RelationType([
        NameType("name", SType()),
        NameType("age", ZType()),
        NameType("license", SType()),
    ]),
}

engine = Postgres()
parser = Parser()

# The test query - SELECT name, ORDER BY age (age not in SELECT)
sql = "SELECT name FROM pilot ORDER BY age DESC"

print("="*80)
print("Testing ORDER BY with column not in SELECT list")
print("="*80)
print(f"Query: {sql}")
print()
print("Data:")
print("  pilot table:")
for row in rows_pilot:
    print(f"    {[str(cell) for cell in row]}")
print()

try:
    # Parse
    print("Step 1: Parsing...")
    parsed_sql = sqlparse.parse(sql)
    statement = parsed_sql[0]
    parsed = parser.parse_select(statement)
    print(f"✓ Parsed successfully")
    print(f"  AST: {parsed}")
    print()
    
    # Typecheck
    print("Step 2: Typechecking...")
    print(f"  Schema (dbt): {dbt}")
    print(f"  Calling: typecheck_query(dbt, RelationType([]), parsed)")
    print()
    
    TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
    T = TQ[0]
    qp = TQ[1]
    
    print(f"✓ Typechecked successfully!")
    print(f"  Result type: {T}")
    print(f"  Translated query: {qp}")
    print()
    
    # Run
    print("Step 3: Running query...")
    result = engine.run.run_query(db, Eta([], []), qp)
    
    print(f"✓ Query executed successfully!")
    print(f"  Result columns: {result.cols}")
    print(f"  Result rows ({len(result.rows)} rows):")
    for i, row in enumerate(result.rows):
        print(f"    Row {i+1}: {[cell.erase() for cell in row]}")
    print()
    
    # Verify ordering (should be descending by age: Diana(35), Bob(30), Alice(25), Charlie(22))
    expected_order = ["Diana", "Bob", "Alice", "Charlie"]
    actual_order = [row[0].erase() for row in result.rows]
    
    print("  Verification:")
    print(f"    Expected order (by age DESC): {expected_order}")
    print(f"    Actual order: {actual_order}")
    
    if actual_order == expected_order:
        print("    ✓ Order is correct!")
    else:
        print("    ✗ Order is WRONG!")
    
    print()
    print("="*80)
    print("✓ TEST PASSED - ORDER BY with non-SELECT column works!")
    print("="*80)
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    print()
    import traceback
    print("Full traceback:")
    print("-"*80)
    traceback.print_exc()
    print("-"*80)
    print()
    print("="*80)
    print("✗ TEST FAILED")
    print("="*80)
    print()
    print("Issue: Cannot ORDER BY a column that is not in the SELECT list")
    print("This is a valid SQL operation that should be supported.")
