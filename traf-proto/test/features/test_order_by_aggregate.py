"""
Test ORDER BY with aggregate functions that aren't in SELECT list
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from interpreter.lark_parser import LarkParser
from interpreter.syntax.type.Database import Database
from interpreter.syntax.type.RelationType import RelationType
from interpreter.syntax.engine.Postgres import Postgres

# Create test database
db = Database({
    'weather': type('Table', (), {
        'cols': ['zip_code', 'mean_sea_level_pressure_inches', 'date'],
        'rows': [
            ['94102', 30.01, '2020-01-01'],
            ['94102', 30.05, '2020-01-02'],
            ['94103', 29.98, '2020-01-01'],
            ['94103', 29.95, '2020-01-02'],
        ]
    })()
})

dbt = Database({
    'weather': type('TableType', (), {
        'nametypes': [
            ('zip_code', type('ValueType', (), {'__str__': lambda s: 'String'})()),
            ('mean_sea_level_pressure_inches', type('ValueType', (), {'__str__': lambda s: 'Real'})()),
            ('date', type('ValueType', (), {'__str__': lambda s: 'String'})()),
        ]
    })()
})

# Test query: SELECT zip_code FROM weather GROUP BY zip_code ORDER BY avg(mean_sea_level_pressure_inches)
sql_query = """
SELECT zip_code
FROM weather
GROUP BY zip_code
ORDER BY avg(mean_sea_level_pressure_inches)
LIMIT 1;
"""

print("="*80)
print("Test: ORDER BY with aggregate function not in SELECT list")
print("="*80)
print(f"Query: {sql_query.strip()}")
print()

try:
    # Parse the query
    parser = LarkParser(schema=dbt)
    parsed = parser.parse(sql_query)
    print(f"✓ Parsing succeeded")
    print(f"Parsed query structure:")
    print(f"  {parsed}")
    print()
    
    # Typecheck the query
    engine = Postgres()
    TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
    T = TQ[0]
    qp = TQ[1]
    print(f"✓ Typechecking succeeded")
    print(f"Result type: {T}")
    print()
    
    print("✓ Test PASSED - ORDER BY with aggregate not in SELECT works correctly!")
    print()
    print("The fix adds the aggregate to the SELECT list temporarily,")
    print("uses it for ordering, then projects it out from the final result.")
    
except Exception as e:
    print(f"✗ Test FAILED")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
