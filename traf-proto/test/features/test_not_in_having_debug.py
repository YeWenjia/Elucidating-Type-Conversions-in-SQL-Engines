#!/usr/bin/env python3
"""
Debug test for NOT IN with subquery containing GROUP BY / HAVING.

Query from bike_1/0022:
  SELECT avg(long)
  FROM station
  WHERE id NOT IN
      (SELECT station_id
       FROM status
       GROUP BY station_id
       HAVING max(bikes_available) > 10)

Expected: avg(long) of stations whose id does not appear in the
          station_ids that ever had more than 10 bikes available.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import yaml
import psycopg2
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.type.RelationType import RelationType
from interpreter.Runtime import Eta

print("=" * 80)
print("Loading data from PostgreSQL (traf_spider.bike_1)")
print("=" * 80)

config_path = project_root / "test" / "config.yml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

postgres_config = config['postgres']
conn = psycopg2.connect(
    host=postgres_config.get('host', 'localhost'),
    port=postgres_config.get('port', 5432),
    dbname='traf_spider',
    user=postgres_config.get('username', 'postgres'),
    password=postgres_config.get('password', '')
)

cursor = conn.cursor()

from test.spider.test_spider_folders import get_all_tables
db, dbt = get_all_tables(conn, 'postgres', 'bike_1')

print(f"Loaded tables: {list(dbt.keys())}")

# Reference result from PostgreSQL
cursor.execute("SET search_path TO bike_1, public")
cursor.execute("""
    SELECT avg(long)
    FROM station
    WHERE id NOT IN (
        SELECT station_id
        FROM status
        GROUP BY station_id
        HAVING max(bikes_available) > 10
    )
""")
expected_result = cursor.fetchone()[0]
print(f"Expected result (PostgreSQL): {expected_result}")
print()

engine = Postgres()
parser = LarkParser(schema=dbt)

sql = """
SELECT avg(long)
FROM station
WHERE id NOT IN
    (SELECT station_id
     FROM status
     GROUP BY station_id
     HAVING max(bikes_available) > 10);
"""

print("=" * 80)
print("Testing NOT IN with GROUP BY / HAVING subquery")
print("=" * 80)
print(f"Query: {sql.strip()}")
print()

try:
    print("Step 1: Parsing...")
    parsed = parser.parse(sql)
    print(f"✓ Parsed: {parsed}")
    print()

    print("Step 2: Typechecking...")
    TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
    T, qp = TQ[0], TQ[1]
    print(f"✓ Type: {T}")
    print(f"  Translated: {qp}")
    print()

    print("Step 3a: Testing subquery independently...")
    subquery_sql = """
    SELECT station_id
    FROM status
    GROUP BY station_id
    HAVING max(bikes_available) > 10;
    """
    parsed_sub = parser.parse(subquery_sql)
    TQ_sub = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed_sub)
    result_sub = engine.run.run_query(db, Eta([], []), TQ_sub[1])
    print(f"  Subquery rows ({len(result_sub.rows)} total): {[row[0].v for row in result_sub.rows[:10]]}")
    print()

    print("Step 3b: Running full query...")
    result = engine.run.run_query(db, Eta([], []), qp)
    print(f"✓ Result columns: {result.cols}")
    print(f"  Result rows: {result.rows}")
    print()

    actual = result.rows[0][0].v if result.rows else None

    print("Comparison:")
    print(f"  PostgreSQL:  {expected_result}")
    print(f"  Interpreter: {actual}")
    print()

    from decimal import Decimal
    match = (
        actual is not None and
        expected_result is not None and
        abs(Decimal(str(actual)) - Decimal(str(expected_result))) < Decimal("0.0001")
    )

    if match:
        print("=" * 80)
        print("✓ TEST PASSED")
        print("=" * 80)
    else:
        print("=" * 80)
        print("✗ TEST FAILED")
        print(f"  Expected: {expected_result}")
        print(f"  Actual:   {actual}")
        print("=" * 80)

except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    print()
    print("Full traceback:")
    print("-" * 80)
    traceback.print_exc()
    print("-" * 80)
    print()
    print("=" * 80)
    print("✗ TEST FAILED - Query execution error")
    print("=" * 80)

finally:
    cursor.close()
    conn.close()
    print("\nDatabase connection closed.")
