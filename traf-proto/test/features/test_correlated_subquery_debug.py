#!/usr/bin/env python3
"""
Debug test for correlated subquery scoping issue.

Query: SELECT * FROM TA WHERE ('Lucas Davis') IN (SELECT TB.fullname FROM TB WHERE TA.name=TB.fullname)

Expected: Should work - the subquery should see TA from outer scope
Actual: Type error - TA is not in scope in the subquery
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.Runtime import Eta
from interpreter.queryGenerator import *
from interpreter.syntax.type.RelationType import RelationType, NameType

# Test data - matching the test_subquery_scoping_issue test
rows_ta = [
    [BValue("Lucas Davis"), BValue(6.0), BValue(31)],
    [BValue("John Doe"), BValue(5.8), BValue(30)],
]
for row in rows_ta:
    for cell in row:
        cell.unknown = False

rows_tb = [
    [BValue(31), BValue("Lucas Davis"), BValue(6.0)],
    [BValue(30), BValue("John Doe"), BValue(5.8)],
]
for row in rows_tb:
    for cell in row:
        cell.unknown = False

db = {
    "TA": Table(["name", "height", "age"], rows_ta),
    "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
}

dbt = {
    "TA": RelationType([
        NameType("name", SType()),
        NameType("height", RType()),
        NameType("age", ZType())
    ]),
    "TB": RelationType([
        NameType("realage", ZType()),
        NameType("fullname", SType()),
        NameType("fullheight", RType())
    ]),
}

engine = Postgres()
parser = LarkParser()

# The problematic query
sql = "SELECT * FROM TA WHERE ('Lucas Davis') IN (SELECT TB.fullname FROM TB WHERE TA.name=TB.fullname)"

print("="*80)
print("Testing Correlated Subquery")
print("="*80)
print(f"Query: {sql}")
print()

try:
    # Parse
    print("Step 1: Parsing...")
    parsed = parser.parse(sql)
    print(f"✓ Parsed successfully: {parsed}")
    print()
    
    # Typecheck
    print("Step 2: Typechecking...")
    print(f"Schema (dbt): {dbt}")
    print(f"Calling: typecheck_query(dbt, RelationType([]), parsed)")
    print()
    
    TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
    T = TQ[0]
    qp = TQ[1]
    
    print(f"✓ Typechecked successfully!")
    print(f"Type: {T}")
    print(f"Translated query: {qp}")
    print()
    
    # Run
    print("Step 3: Running query...")
    result = engine.run.run_query(db, Eta([], []), qp)
    
    print(f"✓ Query executed successfully!")
    print(f"Result columns: {result.cols}")
    print(f"Result rows: {len(result.rows)}")
    for row in result.rows:
        print(f"  {[cell.v for cell in row]}")
    print()
    print("="*80)
    print("✓ TEST PASSED - Correlated subquery works!")
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
    print("✗ TEST FAILED - Correlated subquery not working")
    print("="*80)
    print()
    print("Expected issue: TA.name in the subquery WHERE clause cannot be resolved")
    print("because the typechecker doesn't pass the outer scope (TA) to the subquery.")
