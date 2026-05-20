"""
Fixture for the exhaustive Postgres test.

Connects to the `interpreter` Postgres database (populated out-of-band with
tables ta / tb / tc) and builds the `(conn, db, dbt)` triple the interpreter
needs. No schema creation, no seeding — the tables must exist already.
"""

from pathlib import Path

import psycopg2
import pytest
import yaml

from interpreter.syntax.Table import Table
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.type.Database import Database


CONFIG_PATH = Path(__file__).parent.parent / "config.yml"


def _load_pg_config():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return cfg["postgres"]


TABLES = ("ta", "tb", "tc")


@pytest.fixture(scope="session")
def exhaustive_fixture():
    pg = _load_pg_config()
    conn = psycopg2.connect(
        host=pg.get("host", "localhost"),
        port=pg.get("port", 5432),
        dbname=pg["database"],
        user=pg.get("username"),
        password=pg.get("password") or "",
    )

    engine = Postgres()
    # infer_schema uppercases keys and returns every table in `public`.
    # The enumerator uses lowercase `ta/tb/tc` and the typechecker does exact-
    # match lookup, so we rebuild dbt/db with just those three, lowercased.
    raw = engine.infer_schema(conn)
    dbt = {}
    for name in TABLES:
        key = next((k for k in raw if k.lower() == name), None)
        if key is None:
            raise RuntimeError(f"expected table {name!r} in `interpreter` db; found {list(raw)}")
        dbt[name] = raw[key]

    db = Database({})
    cur = conn.cursor()
    for name, rel_type in dbt.items():
        col_names = [nt.name for nt in rel_type.nametypes]
        cur.execute(f"SELECT {', '.join(col_names)} FROM {name}")
        rows = []
        for raw_row in cur.fetchall():
            row = []
            for v in raw_row:
                bv = BValue(v, True)
                bv.unknown = False
                row.append(bv)
            rows.append(row)
        db[name] = Table(col_names, rows)
    cur.close()

    try:
        yield conn, db, dbt
    finally:
        conn.close()
