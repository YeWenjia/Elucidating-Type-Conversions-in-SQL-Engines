"""
Debug runner for a single SQLancer case against Oracle.

Usage:
    python -m test.sqlancer.run_case_oracle <N>                  # case_NNNNNN.yml in both-fail
    python -m test.sqlancer.run_case_oracle <N> <subdir>         # e.g. dbms-fail, benign
    python -m test.sqlancer.run_case_oracle <path-to-yml>

Loads the yml, materialises the schema on Oracle (same DDL helpers as
test_sqlancer_cases.py), runs the rewritten SQL on Oracle, runs the original
SQL through the Traf interpreter configured for Oracle, and prints both
results plus a comparison.
"""

import sys
from pathlib import Path

from interpreter.syntax.engine.Engine import Engine

from test.sqlancer.test_sqlancer_cases import (
    _get_conn,
    _load_sqlancer_case,
    _materialise_oracle,
    _normalise_sql_for_engine,
    _open_oracle,
    _replace_where_with_constant,
    _rewrite_sql,
    _run_sqlancer_interpreter,
    _set_search_path,
    _sqlancer_oracle_sql_never_true,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SUBDIR = "both-fail"


def resolve_path(arg: str, subdir: str) -> Path:
    p = Path(arg)
    if p.exists():
        return p
    if arg.isdigit():
        n = int(arg)
        return REPO_ROOT / "benchmarks" / "sqlancer" / subdir / f"case_{n:06d}.yml"
    raise FileNotFoundError(f"cannot resolve case from {arg!r}")


def section(title: str):
    print(f"\n=== {title} ===")


def fmt_row(row):
    return [v.erase() if hasattr(v, "erase") else v for v in row]


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(__doc__.strip())
        sys.exit(2)

    arg = sys.argv[1]
    subdir = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_SUBDIR
    case_path = resolve_path(arg, subdir)
    print(f"case: {case_path}")

    case = _load_sqlancer_case(case_path)
    schema_dict = case.get("schema") or {}
    data_dict = case.get("data") or {}
    sql = (case.get("sql") or "").strip()
    if not sql:
        print("no sql in case")
        sys.exit(1)
    if not sql.endswith(";"):
        sql += ";"

    section("schema")
    for tbl, cols in schema_dict.items():
        cs = ", ".join(f"{c['name']}:{c['type']}" for c in cols)
        print(f"  {tbl}({cs})")

    section("data")
    for tbl, rows in data_dict.items():
        print(f"  {tbl}: {len(rows)} rows")
        for r in rows[:5]:
            print(f"    {r}")
        if len(rows) > 5:
            print(f"    ... (+{len(rows) - 5})")

    section("sql (interpreter)")
    print(f"  {sql}")

    db_sql = _normalise_sql_for_engine(
        _rewrite_sql(sql, "oracle", schema_dict), "oracle"
    )
    if _sqlancer_oracle_sql_never_true(sql, schema_dict, data_dict):
        db_sql = _replace_where_with_constant(db_sql, "(1=0)")

    section("sql (oracle, rewritten)")
    print(f"  {db_sql}")

    section("materialise on oracle")
    cache = {}
    conn = _get_conn(cache, "oracle")
    try:
        _materialise_oracle(conn, schema_dict, data_dict)
        print("  ok")
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    section("oracle rows")
    their_result = None
    their_error = None
    try:
        _set_search_path(conn, "oracle")
        cur = conn.cursor()
        cur.execute(db_sql)
        their_result = cur.fetchall()
        for r in their_result[:20]:
            print(f"  {list(r)}")
        if len(their_result) > 20:
            print(f"  ... (+{len(their_result) - 20})")
        print(f"  total: {len(their_result)}")
    except Exception as e:
        their_error = e
        print(f"  ORACLE ERROR: {e}")
    finally:
        try:
            conn.rollback()
        except Exception:
            pass

    section("interpreter rows (normal)")
    our_result, our_error, engine = _run_sqlancer_interpreter(
        sql, schema_dict, data_dict, "oracle"
    )
    if our_error is not None:
        print(f"  INTERPRETER ERROR: {our_error}")
    else:
        for r in our_result.rows[:20]:
            print(f"  {fmt_row(r)}")
        if len(our_result.rows) > 20:
            print(f"  ... (+{len(our_result.rows) - 20})")
        print(f"  total: {len(our_result.rows)}")

    section("interpreter rows (short-circuit)")
    short_result, short_error, _ = _run_sqlancer_interpreter(
        sql, schema_dict, data_dict, "oracle", short_circuit=True
    )
    if short_error is not None:
        print(f"  INTERPRETER ERROR: {short_error}")
    else:
        for r in short_result.rows[:20]:
            print(f"  {fmt_row(r)}")
        if len(short_result.rows) > 20:
            print(f"  ... (+{len(short_result.rows) - 20})")
        print(f"  total: {len(short_result.rows)}")

    section("comparison")
    if their_error is not None and our_error is not None:
        print("  BOTH FAILED (agreement)")
    elif their_error is not None:
        print(f"  ORACLE FAILED but interpreter succeeded")
    elif our_error is not None and (short_error is not None or short_result is None):
        print(f"  INTERPRETER FAILED but oracle succeeded")
    else:
        for label, result in [("normal", our_result), ("short-circuit", short_result)]:
            if result is None:
                continue
            match = Engine().Compare(result.rows, list(their_result), engine)
            print(f"  interpreter ({label}) vs oracle: {'MATCH' if match else 'MISMATCH'}")

    section("recorded in yml")
    print(f"  kind: {case.get('kind')}")
    print(f"  dbms_error: {case.get('dbms_error')}")
    traf_error = case.get('traf_error')
    if traf_error:
        print(f"  traf_error: {traf_error}")

    try:
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
