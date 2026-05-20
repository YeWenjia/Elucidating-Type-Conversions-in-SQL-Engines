"""
Fixtures for Calcite benchmark tests.

The 397 entries in calcite2.jsonlines all share the same schema (six tables:
EMP, DEPT, BONUS, EMPNULLABLES, EMPNULLABLES_20, EMP_B), so the tables are
created and seeded exactly once per engine, lazily on first use.

We compare the interpreter against five real engines (Postgres, MySQL, SQLite,
MSSQL, Oracle). Each engine gets its own dedicated schema/database
(`traf_calcite`) so the test suite never collides with a developer's other
work. Connections are session-scoped and re-used across all parametrised
cases — opening five connections per test would be untenable for 794 queries.
"""

import json
from pathlib import Path

import psycopg2
import pytest
import yaml

try:
    import mysql.connector
except ImportError:
    mysql = None

import datetime as _dt
import sqlite3

# Python 3.12 deprecated the default `datetime.date` adapter for sqlite3.
# Register an explicit ISO-8601 adapter so DATE inserts stop emitting warnings
# and round-trip predictably.
sqlite3.register_adapter(_dt.date, lambda d: d.isoformat())
sqlite3.register_adapter(_dt.datetime, lambda d: d.isoformat(sep=" "))

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import oracledb
except ImportError:
    oracledb = None

from interpreter.Parser import Table
from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.type.RelationType import NameType, RelationType
from interpreter.syntax.type.ValueType import BType, DTType, SType, ZType

from test.calcite.seed_data import TABLE_ROWS


CALCITE_JSONLINES = (
    Path(__file__).parent.parent.parent
    / "benchmarks" / "calcite" / "calcite2.jsonlines"
)
CONFIG_PATH = Path(__file__).parent.parent / "config.yml"
CALCITE_DB = "traf_calcite"
CALCITE_SCHEMA = "calcite"
CALCITE_SQLITE_PATH = Path(__file__).parent.parent.parent / ".calcite_sqlite.db"

ENABLED_ENGINES = ["postgres", "mysql", "sqlite", "mssql", "oracle"]

JSON_TYPE_MAP = {
    "INT": ZType,
    "VARCHAR": SType,
    "DATE": DTType,
    "BOOLEAN": BType,
}

PG_TYPE_MAP = {
    "INT": "INT",
    "VARCHAR": "VARCHAR(64)",
    "DATE": "DATE",
    "BOOLEAN": "BOOLEAN",
}

MYSQL_TYPE_MAP = {
    "INT": "INT",
    "VARCHAR": "VARCHAR(64)",
    "DATE": "DATE",
    "BOOLEAN": "TINYINT(1)",  # MySQL's BOOLEAN is an alias for TINYINT(1)
}

SQLITE_TYPE_MAP = {
    "INT": "INTEGER",
    "VARCHAR": "TEXT",
    "DATE": "DATE",
    "BOOLEAN": "INTEGER",  # SQLite has no native bool — store 0/1
}

MSSQL_TYPE_MAP = {
    "INT": "INT",
    "VARCHAR": "NVARCHAR(64)",
    "DATE": "DATE",
    "BOOLEAN": "BIT",
}

ORACLE_TYPE_MAP = {
    "INT": "NUMBER(10)",
    "VARCHAR": "VARCHAR2(64)",
    "DATE": "DATE",
    "BOOLEAN": "NUMBER(1)",  # Oracle <23c has no real BOOLEAN column type
}


# ---------------------------------------------------------------------------
# CLI options (kept calcite-specific to avoid clashing with the sqlancer
# suite, which already registers --engine in its own conftest).
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--calcite-engine",
        dest="calcite_engines",
        default=None,
        help="Comma-separated list of engines to test "
             "(postgres, mysql, sqlite, mssql, oracle). Default: all.",
    )
    parser.addoption(
        "--calcite-mismatch-report",
        dest="calcite_mismatch_report",
        default="calcite_mismatches.json",
        help=(
            "Path to write the JSON summary/details for Calcite mismatches. "
            "Relative paths are resolved from pytest rootdir. Use an empty "
            "string to disable report writing."
        ),
    )


def pytest_configure(config):
    config._calcite_mismatches = []


def _counter_dict(counter):
    return dict(sorted(counter.items(), key=lambda item: item[0]))


def pytest_sessionfinish(session, exitstatus):
    report_opt = session.config.getoption("calcite_mismatch_report")
    if not report_opt:
        return
    mismatches = getattr(session.config, "_calcite_mismatches", [])
    from collections import Counter
    by_engine = Counter(m["engine"] for m in mismatches)
    by_reason = Counter(m["reason"] for m in mismatches)
    by_engine_reason = Counter(f"{m['engine']}/{m['reason']}" for m in mismatches)

    payload = {
        "summary": {
            "total": len(mismatches),
            "by_engine": _counter_dict(by_engine),
            "by_reason": _counter_dict(by_reason),
            "by_engine_reason": _counter_dict(by_engine_reason),
        },
        "mismatches": mismatches,
    }

    report_path = Path(report_opt)
    if not report_path.is_absolute():
        report_path = Path(session.config.rootpath) / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def pytest_collection_modifyitems(config, items):
    sel = config.getoption("calcite_engines")
    if sel is None:
        return
    wanted = {e.strip() for e in sel.split(",") if e.strip()}
    items[:] = [
        it for it in items
        if not (hasattr(it, "callspec") and "engine_name" in it.callspec.params)
           or it.callspec.params["engine_name"] in wanted
    ]


# ---------------------------------------------------------------------------
# Config + schema introspection
# ---------------------------------------------------------------------------
def _load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _first_entry_schema():
    with open(CALCITE_JSONLINES) as f:
        return json.loads(f.readline())["schema"]


def _build_dbt(schema_json):
    dbt = {}
    for table_name, cols in schema_json.items():
        nametypes = [
            NameType(col, JSON_TYPE_MAP[json_type]())
            for col, json_type in cols.items()
        ]
        dbt[table_name] = RelationType(nametypes)
    return dbt


def _build_db(schema_json):
    db = {}
    for table_name, cols in schema_json.items():
        col_names = list(cols.keys())
        bvalue_rows = []
        for row in TABLE_ROWS[table_name.lower()]:
            bvalue_row = []
            for v in row:
                bv = BValue(v, use_decimal=True)
                bv.unknown = False
                bvalue_row.append(bv)
            bvalue_rows.append(bvalue_row)
        db[table_name] = Table(col_names, bvalue_rows)
    return db


# ---------------------------------------------------------------------------
# Per-engine database/connection setup
# ---------------------------------------------------------------------------
def _ensure_pg_database(pg):
    admin = psycopg2.connect(
        host=pg.get("host", "localhost"),
        port=pg.get("port", 5432),
        dbname="postgres",
        user=pg.get("username"),
        password=pg.get("password") or "",
    )
    admin.autocommit = True
    try:
        cur = admin.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (CALCITE_DB,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{CALCITE_DB}"')
    finally:
        admin.close()


def _ensure_mysql_database(my):
    admin = mysql.connector.connect(
        host=my.get("host", "localhost"),
        port=my.get("port", 3306),
        user=my.get("username", "root"),
        password=my.get("password") or "",
    )
    try:
        cur = admin.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{CALCITE_DB}`")
        admin.commit()
    finally:
        admin.close()


def _ensure_mssql_database(ms):
    admin_str = (
        f"DRIVER={{{ms.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
        f"SERVER={ms.get('server', 'localhost')};"
        f"DATABASE=master;"
        f"UID={ms.get('username', 'sa')};"
        f"PWD={ms.get('password', '')}"
    )
    admin = pyodbc.connect(admin_str, autocommit=True)
    try:
        cur = admin.cursor()
        cur.execute(
            f"IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = '{CALCITE_DB}') "
            f"CREATE DATABASE [{CALCITE_DB}]"
        )
    finally:
        admin.close()


def _open_postgres():
    cfg = _load_config()["postgres"]
    _ensure_pg_database(cfg)
    conn = psycopg2.connect(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5432),
        dbname=CALCITE_DB,
        user=cfg.get("username"),
        password=cfg.get("password") or "",
    )
    cur = conn.cursor()
    cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{CALCITE_SCHEMA}"')
    conn.commit()
    return conn


def _open_mysql():
    if mysql is None:
        pytest.skip("mysql.connector not installed")
    cfg = _load_config()["mysql"]
    _ensure_mysql_database(cfg)
    return mysql.connector.connect(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 3306),
        user=cfg.get("username", "root"),
        password=cfg.get("password") or "",
        database=CALCITE_DB,
    )


def _open_sqlite():
    if CALCITE_SQLITE_PATH.exists():
        CALCITE_SQLITE_PATH.unlink()
    return sqlite3.connect(str(CALCITE_SQLITE_PATH))


def _open_mssql():
    if pyodbc is None:
        pytest.skip("pyodbc not installed")
    cfg = _load_config()["mssql"]
    _ensure_mssql_database(cfg)
    conn_str = (
        f"DRIVER={{{cfg.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
        f"SERVER={cfg.get('server', 'localhost')};"
        f"DATABASE={CALCITE_DB};"
        f"UID={cfg.get('username', 'sa')};"
        f"PWD={cfg.get('password', '')}"
    )
    conn = pyodbc.connect(conn_str, autocommit=False)
    cur = conn.cursor()
    cur.execute(
        f"IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{CALCITE_SCHEMA}') "
        f"EXEC('CREATE SCHEMA [{CALCITE_SCHEMA}]')"
    )
    conn.commit()
    return conn


def _open_oracle():
    if oracledb is None:
        pytest.skip("oracledb not installed")
    cfg = _load_config()["oracle"]
    return oracledb.connect(
        user=cfg.get("user"),
        password=cfg.get("password") or "",
        dsn=cfg.get("dsn"),
    )


_OPENERS = {
    "postgres": _open_postgres,
    "mysql":    _open_mysql,
    "sqlite":   _open_sqlite,
    "mssql":    _open_mssql,
    "oracle":   _open_oracle,
}


# ---------------------------------------------------------------------------
# Per-engine schema + table materialisation (once per session)
# ---------------------------------------------------------------------------
def _coerce_bool(v):
    if v is None:
        return None
    return 1 if v else 0


def _seed_rows_for_engine(cols, table_name, engine_name):
    """Convert TABLE_ROWS into the exact tuples the driver wants.

    Booleans become 0/1 for engines that have no native bool. Everything else
    passes through; date/datetime objects are accepted by all five drivers.
    """
    rows = TABLE_ROWS[table_name.lower()]
    if engine_name in ("sqlite", "oracle"):
        out = []
        for row in rows:
            out.append(tuple(
                _coerce_bool(v) if json_type == "BOOLEAN" else v
                for v, json_type in zip(row, cols.values())
            ))
        return out
    return [tuple(row) for row in rows]


def _materialise_pg(conn, schema_json):
    cur = conn.cursor()
    for table_name in schema_json.keys():
        cur.execute(
            f'DROP TABLE IF EXISTS "{CALCITE_SCHEMA}"."{table_name.lower()}" CASCADE'
        )
    for table_name, cols in schema_json.items():
        col_defs = ", ".join(
            f'"{col.lower()}" {PG_TYPE_MAP[json_type]}'
            for col, json_type in cols.items()
        )
        cur.execute(
            f'CREATE TABLE "{CALCITE_SCHEMA}"."{table_name.lower()}" ({col_defs})'
        )
        rows = _seed_rows_for_engine(cols, table_name, "postgres")
        if rows:
            placeholders = ", ".join(["%s"] * len(cols))
            col_list = ", ".join(f'"{c.lower()}"' for c in cols.keys())
            cur.executemany(
                f'INSERT INTO "{CALCITE_SCHEMA}"."{table_name.lower()}" '
                f'({col_list}) VALUES ({placeholders})',
                rows,
            )
    conn.commit()


def _materialise_mysql(conn, schema_json):
    cur = conn.cursor()
    # Drop in dependency-free order — calcite tables have no FKs.
    for table_name in schema_json.keys():
        cur.execute(f"DROP TABLE IF EXISTS `{table_name.lower()}`")
    for table_name, cols in schema_json.items():
        col_defs = ", ".join(
            f"`{col.lower()}` {MYSQL_TYPE_MAP[json_type]}"
            for col, json_type in cols.items()
        )
        cur.execute(f"CREATE TABLE `{table_name.lower()}` ({col_defs})")
        rows = _seed_rows_for_engine(cols, table_name, "mysql")
        if rows:
            placeholders = ", ".join(["%s"] * len(cols))
            col_list = ", ".join(f"`{c.lower()}`" for c in cols.keys())
            cur.executemany(
                f"INSERT INTO `{table_name.lower()}` ({col_list}) "
                f"VALUES ({placeholders})",
                rows,
            )
    conn.commit()


def _materialise_sqlite(conn, schema_json):
    cur = conn.cursor()
    for table_name in schema_json.keys():
        cur.execute(f'DROP TABLE IF EXISTS "{table_name.lower()}"')
    for table_name, cols in schema_json.items():
        col_defs = ", ".join(
            f'"{col.lower()}" {SQLITE_TYPE_MAP[json_type]}'
            for col, json_type in cols.items()
        )
        cur.execute(f'CREATE TABLE "{table_name.lower()}" ({col_defs})')
        rows = _seed_rows_for_engine(cols, table_name, "sqlite")
        if rows:
            placeholders = ", ".join(["?"] * len(cols))
            col_list = ", ".join(f'"{c.lower()}"' for c in cols.keys())
            cur.executemany(
                f'INSERT INTO "{table_name.lower()}" ({col_list}) '
                f'VALUES ({placeholders})',
                rows,
            )
    conn.commit()


def _materialise_mssql(conn, schema_json):
    cur = conn.cursor()
    for table_name in schema_json.keys():
        cur.execute(
            f"IF OBJECT_ID('[{CALCITE_SCHEMA}].[{table_name.lower()}]', 'U') IS NOT NULL "
            f"DROP TABLE [{CALCITE_SCHEMA}].[{table_name.lower()}]"
        )
    for table_name, cols in schema_json.items():
        col_defs = ", ".join(
            f'[{col.lower()}] {MSSQL_TYPE_MAP[json_type]}'
            for col, json_type in cols.items()
        )
        cur.execute(
            f"CREATE TABLE [{CALCITE_SCHEMA}].[{table_name.lower()}] ({col_defs})"
        )
        rows = _seed_rows_for_engine(cols, table_name, "mssql")
        if rows:
            placeholders = ", ".join(["?"] * len(cols))
            col_list = ", ".join(f"[{c.lower()}]" for c in cols.keys())
            cur.executemany(
                f"INSERT INTO [{CALCITE_SCHEMA}].[{table_name.lower()}] "
                f"({col_list}) VALUES ({placeholders})",
                rows,
            )
    conn.commit()


def _materialise_oracle(conn, schema_json):
    cur = conn.cursor()
    for table_name in schema_json.keys():
        try:
            cur.execute(f'DROP TABLE "{table_name.upper()}" CASCADE CONSTRAINTS')
        except Exception:
            pass  # didn't exist
    for table_name, cols in schema_json.items():
        col_defs = ", ".join(
            f'"{col.upper()}" {ORACLE_TYPE_MAP[json_type]}'
            for col, json_type in cols.items()
        )
        cur.execute(f'CREATE TABLE "{table_name.upper()}" ({col_defs})')
        rows = _seed_rows_for_engine(cols, table_name, "oracle")
        if rows:
            placeholders = ", ".join(f":{i+1}" for i in range(len(cols)))
            col_list = ", ".join(f'"{c.upper()}"' for c in cols.keys())
            cur.executemany(
                f'INSERT INTO "{table_name.upper()}" ({col_list}) '
                f'VALUES ({placeholders})',
                rows,
            )
    conn.commit()


_MATERIALISERS = {
    "postgres": _materialise_pg,
    "mysql":    _materialise_mysql,
    "sqlite":   _materialise_sqlite,
    "mssql":    _materialise_mssql,
    "oracle":   _materialise_oracle,
}


# ---------------------------------------------------------------------------
# Session-scoped cache of (conn, dbt, db) per engine
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def calcite_engines():
    """Lazy per-engine cache. Each engine is opened + materialised on first use."""
    schema_json = _first_entry_schema()
    dbt = _build_dbt(schema_json)
    db = _build_db(schema_json)
    cache: dict = {}

    def get(engine_name):
        if engine_name in cache:
            return cache[engine_name]
        conn = _OPENERS[engine_name]()
        _MATERIALISERS[engine_name](conn, schema_json)
        cache[engine_name] = (conn, db, dbt)
        return cache[engine_name]

    yield get

    for conn, _, _ in cache.values():
        try:
            conn.close()
        except Exception:
            pass


# Backwards-compatible Postgres-only fixture, kept so callers that import
# `calcite_fixture` (the original API) keep working unchanged.
@pytest.fixture(scope="session")
def calcite_fixture(calcite_engines):
    return calcite_engines("postgres")
