#!/usr/bin/env python3
"""Test BETWEEN operator implementation"""

from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.Parser import Table
from interpreter.Runtime import Eta
from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.type.RelationType import RelationType, NameType

# Create test data
test_data = Table(
    ['name', 'elevation'],
    [
        [BValue('Airport A', use_decimal=True), BValue(-100, use_decimal=True)],
        [BValue('Airport B', use_decimal=True), BValue(-50, use_decimal=True)],
        [BValue('Airport C', use_decimal=True), BValue(-25, use_decimal=True)],
        [BValue('Airport D', use_decimal=True), BValue(0, use_decimal=True)],
        [BValue('Airport E', use_decimal=True), BValue(25, use_decimal=True)],
        [BValue('Airport F', use_decimal=True), BValue(50, use_decimal=True)],
        [BValue('Airport G', use_decimal=True), BValue(100, use_decimal=True)],
    ]
)

db = {'airports': test_data}
schema = {
    'airports': type('RelationType', (), {
        'getColNames': lambda: ['name', 'elevation'],
        'nametypes': []
    })()
}

# Test 1: BETWEEN
print("Test 1: BETWEEN -50 AND 50")
parser = LarkParser(schema=schema)
engine = Postgres()

sql = "SELECT name FROM airports WHERE elevation BETWEEN -50 AND 50"
parsed = parser.parse(sql)
print(f"Parsed: {parsed}")

TQ = engine.typechecker.typecheck_query(schema, RelationType([]), parsed)
result = engine.run.run_query(db, Eta([], []), TQ[1])
print(f"Result: {[row[0].val for row in result.rows]}")
print(f"Expected: ['Airport B', 'Airport C', 'Airport D', 'Airport E', 'Airport F']")
print(f"Match: {[row[0].val for row in result.rows] == ['Airport B', 'Airport C', 'Airport D', 'Airport E', 'Airport F']}")

# Test 2: NOT BETWEEN
print("\nTest 2: NOT BETWEEN -50 AND 50")
sql2 = "SELECT name FROM airports WHERE elevation NOT BETWEEN -50 AND 50"
parsed2 = parser.parse(sql2)
print(f"Parsed: {parsed2}")

TQ2 = engine.typechecker.typecheck_query(schema, RelationType([]), parsed2)
result2 = engine.run.run_query(db, Eta([], []), TQ2[1])
print(f"Result: {[row[0].val for row in result2.rows]}")
print(f"Expected: ['Airport A', 'Airport G']")
print(f"Match: {[row[0].val for row in result2.rows] == ['Airport A', 'Airport G']}")

# Test 3: BETWEEN with negative numbers
print("\nTest 3: BETWEEN -100 AND -25")
sql3 = "SELECT name FROM airports WHERE elevation BETWEEN -100 AND -25"
parsed3 = parser.parse(sql3)
TQ3 = engine.typechecker.typecheck_query(schema, RelationType([]), parsed3)
result3 = engine.run.run_query(db, Eta([], []), TQ3[1])
print(f"Result: {[row[0].val for row in result3.rows]}")
print(f"Expected: ['Airport A', 'Airport B', 'Airport C']")
print(f"Match: {[row[0].val for row in result3.rows] == ['Airport A', 'Airport B', 'Airport C']}")

print("\n✓ All BETWEEN tests completed!")
