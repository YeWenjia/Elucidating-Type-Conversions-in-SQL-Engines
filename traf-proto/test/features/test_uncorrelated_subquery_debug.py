#!/usr/bin/env python3
"""
Debug test for uncorrelated subquery with IN clause.

Query from allergy_1/0046:
  select count(*)
  from student
  where sex = 'M'
    and stuid in
      (select stuid
       from has_allergy t1
       join allergy_type t2 on t1.allergy = t2.allergy
       where t2.allergytype = 'food')

Expected: 10 male students with food allergies
Issue: Interpreter returns 24 (all male students) - subquery executes with wrong environment
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.Runtime import Eta

print("="*80)
print("Loading data from PostgreSQL (traf_spider.allergy_1)")
print("="*80)

# Load config
config_path = project_root / "test" / "config.yml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Connect to PostgreSQL
postgres_config = config['postgres']
conn = psycopg2.connect(
    host=postgres_config.get('host', 'localhost'),
    port=postgres_config.get('port', 5432),
    dbname='traf_spider',
    user=postgres_config.get('username', 'postgres'),
    password=postgres_config.get('password', '')
)

cursor = conn.cursor()

# Load schema and data using the test framework's function
from test.spider.test_spider_folders import get_all_tables
db, dbt = get_all_tables(conn, 'postgres', 'allergy_1')

print(f"Loaded schema with tables: {list(dbt.keys())}")
print(f"Loaded data for tables: {list(db.keys())}")

# Initialize parser with schema (IMPORTANT for table alias resolution!)
parser = LarkParser(schema=dbt)

# Get some statistics
cursor.execute("SELECT COUNT(*) FROM allergy_1.student WHERE sex = 'M'")
male_count = cursor.fetchone()[0]
print(f"Total male students: {male_count}")

cursor.execute("""
    SELECT COUNT(DISTINCT stuid)
    FROM allergy_1.has_allergy t1
    JOIN allergy_1.allergy_type t2 ON t1.allergy = t2.allergy
    WHERE t2.allergytype = 'food'
""")
food_allergy_count = cursor.fetchone()[0]
print(f"Students with food allergies: {food_allergy_count}")

cursor.execute("""
    SELECT COUNT(*)
    FROM allergy_1.student
    WHERE sex = 'M'
      AND stuid IN (
        SELECT stuid
        FROM allergy_1.has_allergy t1
        JOIN allergy_1.allergy_type t2 ON t1.allergy = t2.allergy
        WHERE t2.allergytype = 'food'
      )
""")
expected_result = cursor.fetchone()[0]
print(f"Expected result (from PostgreSQL): {expected_result}")
print()

engine = Postgres()

# The query - uncorrelated subquery (should execute independently)
sql = """
select count(*)
from student
where sex = 'M'
  and stuid in
    (select stuid
     from has_allergy t1
     join allergy_type t2 on t1.allergy = t2.allergy
     where t2.allergytype = 'food')
"""

print("="*80)
print("Testing Uncorrelated Subquery (IN with JOIN)")
print("="*80)
print(f"Query: {sql.strip()}")
print()

print("Expected Behavior:")
print(f"  - Subquery returns students with food allergies")
print(f"  - Male students total: {male_count}")
print(f"  - Expected COUNT(*): {expected_result}")
print()

print("Bug Behavior (if subquery uses outer eta):")
print("  - For each male student, the subquery sees their stuid")
print("  - Subquery returns [stuid, stuid, stuid, ...] for that student")
print("  - IN clause always returns True")
print(f"  - COUNT(*) returns: {male_count} (all male students)")
print()

try:
    # Parse
    print("Step 1: Parsing...")
    parsed = parser.parse(sql)
    print(f"✓ Parsed successfully")
    print(f"  Structure: {type(parsed).__name__}")
    print()
    
    # Typecheck
    print("Step 2: Typechecking...")
    from interpreter.syntax.type.RelationType import RelationType
    TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
    T = TQ[0]
    qp = TQ[1]
    
    print(f"✓ Typechecked successfully!")
    print(f"  Type: {T}")
    print()
    
    # First, let's test the subquery independently
    print("Step 3a: Testing subquery independently...")
    subquery_sql = """
    select stuid
    from has_allergy t1
    join allergy_type t2 on t1.allergy = t2.allergy
    where t2.allergytype = 'food'
    """
    parsed_sub = parser.parse(subquery_sql)
    TQ_sub = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed_sub)
    qp_sub = TQ_sub[1]
    
    result_sub = engine.run.run_query(db, Eta([], []), qp_sub)
    print(f"  Subquery result (first 10): {[row[0].v for row in result_sub.rows[:10]]}")
    print(f"  Number of rows: {len(result_sub.rows)}")
    print()
    
    # Run the full query
    print("Step 3b: Running full query...")
    result = engine.run.run_query(db, Eta([], []), qp)
    
    print(f"✓ Query executed!")
    print(f"  Result columns: {result.cols}")
    print(f"  Result rows: {len(result.rows)}")
    print(f"  COUNT(*) value: {result.rows[0][0].v}")
    print()
    
    # Verify result
    actual_count = result.rows[0][0].v
    
    print(f"Comparison:")
    print(f"  PostgreSQL result: {expected_result}")
    print(f"  Interpreter result: {actual_count}")
    print()
    
    if actual_count == expected_result:
        print("="*80)
        print("✓ TEST PASSED - Uncorrelated subquery works correctly!")
        print("="*80)
    else:
        print("="*80)
        print(f"✗ TEST FAILED - Wrong count!")
        print(f"  Expected: {expected_result}")
        print(f"  Actual:   {actual_count}")
        print("="*80)
        print()
        print("Diagnosis:")
        if actual_count == male_count:
            print("  - Subquery is executing with outer query's eta")
            print("  - This causes it to see outer row's stuid value")
            print("  - Result: IN clause always returns True for rows being tested")
            print("  - Fix: Subquery should execute with Eta([], []) for uncorrelated case")
        elif actual_count > expected_result:
            print("  - Subquery returning duplicate values or other issue")
        print()
    
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
    print("✗ TEST FAILED - Query execution error")
    print("="*80)

finally:
    # Clean up connection
    cursor.close()
    conn.close()
    print("\nDatabase connection closed.")
