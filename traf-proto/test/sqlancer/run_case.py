"""
Debug runner for a single sqlancer case.

Usage:
    python -m test.sqlancer.run_case <path-to-yml>
    python -m test.sqlancer.run_case <N>                 # case_NNNNNN.yml in postgres-traf-mismatch
    python -m test.sqlancer.run_case <N> <subdir>        # case_NNNNNN.yml in benchmarks/sqlancer/<subdir>

Loads the yml in-memory (no Postgres connection), builds the interpreter db/dbt,
runs the query through the Lark parser, typechecker, and runtime, and prints:
    schema, data preview, SQL, parsed AST, typechecked AST,
    interpreter rows, engine rows from yml, previous traf rows from yml,
    and match indicators.
"""

import sys
import traceback
from pathlib import Path

import yaml

from interpreter.Runtime import Eta
from interpreter.lark_parser import LarkParser
from interpreter.syntax.Table import Table
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.type.Database import Database
from interpreter.syntax.type.RelationType import NameType, RelationType
from interpreter.syntax.type.ValueType import SType, ZType


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SUBDIR = "postgres-traf-mismatch"
TYPE_MAP = {"int": ZType, "string": SType}


def resolve_path(arg: str, subdir: str = DEFAULT_SUBDIR) -> Path:
    p = Path(arg)
    if p.exists():
        return p
    if arg.isdigit():
        n = int(arg)
        return REPO_ROOT / "benchmarks" / "sqlancer" / subdir / f"case_{n:06d}.yml"
    raise FileNotFoundError(f"cannot resolve case from {arg!r}")


def build_db(case: dict) -> tuple[dict, Database]:
    dbt: dict = {}
    db = Database({})
    for tbl, cols in case["schema"].items():
        nametypes = [NameType(c["name"], TYPE_MAP[c["type"]]()) for c in cols]
        dbt[tbl] = RelationType(nametypes)
        col_names = [c["name"] for c in cols]

        rows = []
        for raw in case.get("data", {}).get(tbl, []):
            row = []
            for v in raw:
                bv = BValue(v, True)
                bv.unknown = False
                row.append(bv)
            rows.append(row)
        db[tbl] = Table(col_names, rows)
    return dbt, db


def fmt_row(row, erase=True):
    if erase:
        return [v.erase() if hasattr(v, "erase") else v for v in row]
    return list(row)


def section(title: str):
    print(f"\n=== {title} ===")


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(__doc__.strip())
        sys.exit(2)

    arg = sys.argv[1]
    subdir = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_SUBDIR
    case_path = resolve_path(arg, subdir)
    print(f"case: {case_path}")

    with open(case_path) as f:
        case = yaml.safe_load(f)

    section("schema")
    for tbl, cols in case["schema"].items():
        cs = ", ".join(f"{c['name']}:{c['type']}" for c in cols)
        print(f"  {tbl}({cs})")

    section("data")
    for tbl, rows in case.get("data", {}).items():
        print(f"  {tbl}: {len(rows)} rows")
        for r in rows[:5]:
            print(f"    {r}")
        if len(rows) > 5:
            print(f"    ... (+{len(rows) - 5})")

    section("sql")
    sql = case["sql"]
    print(f"  {sql}")
    sql_terminated = sql if sql.rstrip().endswith(";") else sql + ";"

    dbt, db = build_db(case)
    engine = Postgres()
    parser = LarkParser(schema=dbt)

    section("parsed AST")
    try:
        parsed = parser.parse(sql_terminated)
        print(f"  {parsed}")
    except Exception:
        traceback.print_exc()
        return

    section("typechecked AST")
    try:
        TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
        T, qp = TQ[0], TQ[1]
        print(f"  type: {T}")
        print(f"  query: {qp}")
    except Exception:
        traceback.print_exc()
        return

    section("interpreter rows")
    interp_rows = None
    try:
        result = engine.run.run_query(db, Eta([], []), qp)
        interp_rows = [fmt_row(r) for r in result.rows]
        for r in interp_rows[:20]:
            print(f"  {r}")
        if len(interp_rows) > 20:
            print(f"  ... (+{len(interp_rows) - 20})")
        print(f"  total: {len(interp_rows)}")
    except Exception:
        traceback.print_exc()

    section("postgres rows (from yml)")
    pg_rows = case.get("rows", []) or []
    for r in pg_rows[:20]:
        print(f"  {r}")
    if len(pg_rows) > 20:
        print(f"  ... (+{len(pg_rows) - 20})")
    print(f"  total: {len(pg_rows)}")

    section("traf rows (from yml, recorded at gen time)")
    traf_rows = case.get("traf_rows", []) or []
    for r in traf_rows[:20]:
        print(f"  {r}")
    if len(traf_rows) > 20:
        print(f"  ... (+{len(traf_rows) - 20})")
    print(f"  total: {len(traf_rows)}")

    if interp_rows is not None:
        section("comparison")
        cmp_engine = Engine().Compare([result.rows[i] for i in range(len(result.rows))],
                                      [list(r) for r in pg_rows], engine)
        cmp_traf = (interp_rows == [list(r) for r in traf_rows])
        print(f"  interpreter vs postgres : {'MATCH' if cmp_engine else 'MISMATCH'}")
        print(f"  interpreter vs traf_rows: {'MATCH' if cmp_traf else 'MISMATCH'}")


if __name__ == "__main__":
    main()
