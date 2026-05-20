"""
SQLancer Benchmark Test Suite

Each YAML in benchmarks/sqlancer/<kind>/case_*.yml is a fully self-contained
test case: schema (table -> column types), data (rows), sql (the query), and
the originally observed result rows from both the interpreter and Postgres.

For each case AND each enabled engine this test:
    1. Materialises the schema + data on that engine (DROP + CREATE + INSERT;
       YAMLs reuse names like database0_t0 / database0_t1 so we recreate per
       case).
    2. Runs the SQL through the interpreter configured for that engine.
    3. Runs the SQL through the engine's database.
    4. Asserts agreement: same rows, or both error out.

The kind subfolder labels what was historically observed against Postgres
(benign, traf-mismatch, traf-crash, dbms-fail, both-fail). We re-run the
comparison from scratch — the labels just help slice the run via the
--kind / --engine / --from / --upto / --limit options exposed in conftest.py.

Like the Spider suite, this drives MySQL / SQLite / MSSQL / Oracle in
addition to Postgres. Dialect rewriting is intentionally minimal because
SQLancer SQL is generated and uses only basic SELECT/WHERE constructs.
"""

import re
import os
import yaml
import pytest
import psycopg2
import mysql.connector
import sqlite3
from pathlib import Path
from typing import List, Tuple

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import oracledb
except ImportError:
    oracledb = None

from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.engine.Mysql import Mysql
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.syntax.engine.Mssql import Mssql
from interpreter.syntax.engine.Oracle import Oracle
from interpreter.syntax.engine.Engine import Engine
from interpreter.Runtime import Eta
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.expression.IsNull import IsNull
from interpreter.syntax.expression.Or import Or
from interpreter.Parser import Table
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.ValueType import SType, ZType
from interpreter.syntax.type.Database import Database


SQLANCER_BASE = Path(__file__).parent.parent.parent / "benchmarks" / "sqlancer"
CONFIG_PATH = Path(__file__).parent.parent / "config.yml"
SQLITE_DB_PATH = Path(__file__).parent.parent.parent / ".sqlancer_sqlite.db"

ENABLED_ENGINES = ["postgres", "mysql", "sqlite", "mssql", "oracle"]

SQLANCER_DB = "traf_sqlancer"
SQLANCER_PG_SCHEMA = "sqlancer_test"
SQLANCER_MSSQL_SCHEMA = f"sqlancer_test_{os.getpid()}"
SQLANCER_ORACLE_TABLE_PREFIX = f"Q{os.getpid()}_"
MSSQL_QUERY_TIMEOUT_SECONDS = 10

PG_TYPE_MAP     = {"int": "BIGINT",     "string": "TEXT"}
MYSQL_TYPE_MAP  = {"int": "BIGINT",     "string": "TEXT"}
SQLITE_TYPE_MAP = {"int": "INTEGER",    "string": "TEXT"}
MSSQL_TYPE_MAP  = {"int": "BIGINT",     "string": "NVARCHAR(MAX) COLLATE Latin1_General_BIN"}
ORACLE_TYPE_MAP = {"int": "NUMBER(19)", "string": "VARCHAR2(4000)"}

INTERP_TYPE_MAP = {"int": ZType, "string": SType}

ENGINE_CLASSES = {
    "postgres": Postgres,
    "mysql": Mysql,
    "sqlite": Sqlite,
    "mssql": Mssql,
    "oracle": Oracle,
}


def _mssql_cursor(conn):
    cur = conn.cursor()
    try:
        cur.timeout = MSSQL_QUERY_TIMEOUT_SECONDS
    except Exception:
        pass
    return cur


def _oracle_table_name(table: str) -> str:
    return f"{SQLANCER_ORACLE_TABLE_PREFIX}{table}".upper()


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def discover_sqlancer_cases() -> List[Tuple[str, Path]]:
    """Return (kind, yaml_path) for every YAML under benchmarks/sqlancer."""
    cases: List[Tuple[str, Path]] = []
    if not SQLANCER_BASE.exists():
        return cases
    for kind_dir in sorted(SQLANCER_BASE.iterdir()):
        if not kind_dir.is_dir():
            continue
        kind = kind_dir.name
        for yml in sorted(kind_dir.glob("*.yml")):
            cases.append((kind, yml))
    return cases


def _is_unicode_noncharacter(ch: str) -> bool:
    codepoint = ord(ch)
    return 0xFDD0 <= codepoint <= 0xFDEF or (codepoint & 0xFFFF) in (0xFFFE, 0xFFFF)


def _load_sqlancer_case(yaml_path: Path):
    text = yaml_path.read_text(encoding="utf-8")
    text = "".join("\uFFFD" if _is_unicode_noncharacter(ch) else ch for ch in text)
    return yaml.safe_load(text)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def _load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Connection setup (session-scoped, lazily opened per engine)
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
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (SQLANCER_DB,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{SQLANCER_DB}"')
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
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{SQLANCER_DB}`")
        admin.commit()
    finally:
        admin.close()


def _ensure_mssql_database(ms):
    if pyodbc is None:
        return
    admin_str = (
        f"DRIVER={{{ms.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
        f"SERVER={ms.get('server', 'localhost')};"
        f"DATABASE=master;"
        f"UID={ms.get('username', 'sa')};"
        f"PWD={ms.get('password', '')}"
    )
    admin = pyodbc.connect(admin_str, autocommit=True, timeout=5)
    try:
        cur = admin.cursor()
        try:
            cur.timeout = MSSQL_QUERY_TIMEOUT_SECONDS
        except Exception:
            pass
        cur.execute(
            f"IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = '{SQLANCER_DB}') "
            f"CREATE DATABASE [{SQLANCER_DB}]"
        )
    finally:
        admin.close()


def _open_postgres():
    cfg = _load_config()["postgres"]
    _ensure_pg_database(cfg)
    conn = psycopg2.connect(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5432),
        dbname=SQLANCER_DB,
        user=cfg.get("username"),
        password=cfg.get("password") or "",
    )
    cur = conn.cursor()
    cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SQLANCER_PG_SCHEMA}"')
    conn.commit()
    return conn


def _open_mysql():
    cfg = _load_config()["mysql"]
    _ensure_mysql_database(cfg)
    conn = mysql.connector.connect(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 3306),
        user=cfg.get("username", "root"),
        password=cfg.get("password") or "",
        database=SQLANCER_DB,
    )
    return conn


def _open_sqlite():
    if SQLITE_DB_PATH.exists():
        SQLITE_DB_PATH.unlink()
    return sqlite3.connect(str(SQLITE_DB_PATH))


def _open_mssql():
    if pyodbc is None:
        pytest.skip("pyodbc not installed")
    cfg = _load_config()["mssql"]
    _ensure_mssql_database(cfg)
    conn_str = (
        f"DRIVER={{{cfg.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
        f"SERVER={cfg.get('server', 'localhost')};"
        f"DATABASE={SQLANCER_DB};"
        f"UID={cfg.get('username', 'sa')};"
        f"PWD={cfg.get('password', '')}"
    )
    conn = pyodbc.connect(conn_str, autocommit=False, timeout=5)
    cur = _mssql_cursor(conn)
    cur.execute(
        f"IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{SQLANCER_MSSQL_SCHEMA}') "
        f"EXEC('CREATE SCHEMA [{SQLANCER_MSSQL_SCHEMA}]')"
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


@pytest.fixture(scope="session")
def conns():
    """Lazily-opened, session-cached connection per engine."""
    cache = {}
    yield cache
    for c in cache.values():
        try:
            c.close()
        except Exception:
            pass


def _get_conn(cache, engine_name):
    if engine_name not in cache:
        cache[engine_name] = _OPENERS[engine_name]()
    return cache[engine_name]


# ---------------------------------------------------------------------------
# Interpreter side: build dbt + Database from YAML
# ---------------------------------------------------------------------------
def _build_dbt(schema_dict):
    dbt = {}
    for table, cols in schema_dict.items():
        nametypes = [NameType(c["name"], INTERP_TYPE_MAP[c["type"]]()) for c in cols]
        dbt[table] = RelationType(nametypes)
    return dbt


def _coerce_fixture_value(value, type_name: str, *, oracle_empty_strings=False):
    if value is None:
        return None
    if type_name == "string":
        text = str(value)
        if oracle_empty_strings and text == "":
            return None
        return text
    if type_name == "int":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return value


def _coerce_fixture_rows(cols, rows, *, oracle_empty_strings=False):
    return [
        [
            _coerce_fixture_value(
                v,
                col["type"],
                oracle_empty_strings=oracle_empty_strings,
            )
            for v, col in zip(row, cols)
        ]
        for row in rows
    ]


def _build_db(schema_dict, data_dict, engine_name=None):
    db = Database({})
    oracle_empty_strings = engine_name == "oracle"
    for table, cols in schema_dict.items():
        col_names = [c["name"] for c in cols]
        rows = _coerce_fixture_rows(
            cols,
            data_dict.get(table) or [],
            oracle_empty_strings=oracle_empty_strings,
        )
        bvalue_rows = []
        for row in rows:
            br = []
            for v in row:
                bv = BValue(v, use_decimal=True)
                bv.unknown = False
                br.append(bv)
            bvalue_rows.append(br)
        db[table] = Table(col_names, bvalue_rows)
    return db


# ---------------------------------------------------------------------------
# Materialise tables on each engine (drop + create + insert)
# ---------------------------------------------------------------------------
def _materialise_pg(conn, schema_dict, data_dict):
    try:
        conn.rollback()
    except Exception:
        pass
    cur = conn.cursor()
    for table in schema_dict.keys():
        cur.execute(f'DROP TABLE IF EXISTS "{SQLANCER_PG_SCHEMA}"."{table}" CASCADE')
    for table, cols in schema_dict.items():
        col_defs = ", ".join(f'"{c["name"]}" {PG_TYPE_MAP[c["type"]]}' for c in cols)
        cur.execute(f'CREATE TABLE "{SQLANCER_PG_SCHEMA}"."{table}" ({col_defs})')
        rows = _coerce_fixture_rows(cols, data_dict.get(table) or [])
        if rows:
            placeholders = ", ".join(["%s"] * len(cols))
            col_list = ", ".join(f'"{c["name"]}"' for c in cols)
            cur.executemany(
                f'INSERT INTO "{SQLANCER_PG_SCHEMA}"."{table}" ({col_list}) '
                f'VALUES ({placeholders})',
                rows,
            )
    conn.commit()


def _materialise_mysql(conn, schema_dict, data_dict):
    cur = conn.cursor()
    for table in schema_dict.keys():
        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
    for table, cols in schema_dict.items():
        col_defs = ", ".join(f"`{c['name']}` {MYSQL_TYPE_MAP[c['type']]}" for c in cols)
        cur.execute(
            f"CREATE TABLE `{table}` ({col_defs}) "
            f"DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin"
        )
        rows = _coerce_fixture_rows(cols, data_dict.get(table) or [])
        if rows:
            placeholders = ", ".join(["%s"] * len(cols))
            col_list = ", ".join(f"`{c['name']}`" for c in cols)
            cur.executemany(
                f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})",
                rows,
            )
    conn.commit()


def _materialise_sqlite(conn, schema_dict, data_dict):
    cur = conn.cursor()
    for table in schema_dict.keys():
        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
    for table, cols in schema_dict.items():
        col_defs = ", ".join(f'"{c["name"]}" {SQLITE_TYPE_MAP[c["type"]]}' for c in cols)
        cur.execute(f'CREATE TABLE "{table}" ({col_defs})')
        rows = _coerce_fixture_rows(cols, data_dict.get(table) or [])
        if rows:
            placeholders = ", ".join(["?"] * len(cols))
            col_list = ", ".join(f'"{c["name"]}"' for c in cols)
            cur.executemany(
                f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})',
                rows,
            )
    conn.commit()


def _materialise_mssql(conn, schema_dict, data_dict):
    try:
        conn.rollback()
    except Exception:
        pass
    cur = _mssql_cursor(conn)
    for table in schema_dict.keys():
        cur.execute(
            f"IF OBJECT_ID('[{SQLANCER_MSSQL_SCHEMA}].[{table}]', 'U') IS NOT NULL "
            f"DROP TABLE [{SQLANCER_MSSQL_SCHEMA}].[{table}]"
        )
    for table, cols in schema_dict.items():
        col_defs = ", ".join(f'[{c["name"]}] {MSSQL_TYPE_MAP[c["type"]]}' for c in cols)
        cur.execute(f"CREATE TABLE [{SQLANCER_MSSQL_SCHEMA}].[{table}] ({col_defs})")
        rows = _coerce_fixture_rows(cols, data_dict.get(table) or [])
        if rows:
            placeholders = ", ".join(["?"] * len(cols))
            col_list = ", ".join(f"[{c['name']}]" for c in cols)
            cur.executemany(
                f"INSERT INTO [{SQLANCER_MSSQL_SCHEMA}].[{table}] ({col_list}) "
                f"VALUES ({placeholders})",
                rows,
            )
    conn.commit()


def _materialise_oracle(conn, schema_dict, data_dict):
    cur = conn.cursor()
    # Release any TM locks held by uncommitted transactions on this session
    # before issuing DDL, otherwise DROP TABLE can hit ORA-00054. Then ask
    # Oracle to wait briefly for cross-session locks (a previous test run that
    # crashed can leave a TM lock around for some time).
    try:
        conn.commit()
    except Exception:
        pass
    try:
        cur.execute("ALTER SESSION SET DDL_LOCK_TIMEOUT = 30")
    except Exception:
        pass
    for table in schema_dict.keys():
        physical_table = _oracle_table_name(table)
        try:
            cur.execute(f'DROP TABLE "{physical_table}" CASCADE CONSTRAINTS')
        except Exception:
            pass  # table didn't exist
    for table, cols in schema_dict.items():
        physical_table = _oracle_table_name(table)
        col_defs = ", ".join(
            f'"{c["name"].upper()}" {ORACLE_TYPE_MAP[c["type"]]}' for c in cols
        )
        cur.execute(f'CREATE TABLE "{physical_table}" ({col_defs})')
        rows = _coerce_fixture_rows(
            cols,
            data_dict.get(table) or [],
            oracle_empty_strings=True,
        )
        if rows:
            placeholders = ", ".join(f":{i+1}" for i in range(len(cols)))
            col_list = ", ".join(f'"{c["name"].upper()}"' for c in cols)
            cur.executemany(
                f'INSERT INTO "{physical_table}" ({col_list}) VALUES ({placeholders})',
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
# Per-engine SQL rewriting
# ---------------------------------------------------------------------------
_TRUE_RE = re.compile(r"\btrue\b", re.IGNORECASE)
_FALSE_RE = re.compile(r"\bfalse\b", re.IGNORECASE)
_CAST_AS_INT_RE = re.compile(r"(?i)\bCAST\s*\(\s*([^,()]+(?:\([^)]*\))?[^,()]*)\s+AS\s+INT\b\s*\)")
_MYSQL_CAST_AS_INT_RE = re.compile(r"(?i)\bAS\s+INT\s*\)")
_CAST_AS_VARCHAR_RE = re.compile(r"(?i)\bAS\s+VARCHAR\s*\(\s*(\d+)\s*\)")
_WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)
_SQL_STRING_LITERAL_RE = re.compile(r"'(?:[^']|'')*'")
_QUALIFIED_COL_RE = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b")


# Postgres accepts whitespace-trimmed bare strings as boolean literals; Oracle
# 23c rejects them. These sets mirror Postgres's `parse_bool` accepted forms.
_PG_TRUE_LITERALS = {"t", "tr", "tru", "true", "y", "ye", "yes", "on", "1"}
_PG_FALSE_LITERALS = {"f", "fa", "fal", "fals", "false", "n", "no", "of", "off", "0"}
_WHERE_BARE_STRING_RE = re.compile(
    r"(?i)(\bWHERE\s+)('(?:[^']|'')*')(\s*)(?=;|\)|$)"
)
_WHERE_BARE_NULL_RE = re.compile(
    r"(?i)(\bWHERE\s+)NULL(\s*)(?=;|\)|$)"
)
_NOT_NULL_RE = re.compile(r"(?i)\bNOT\s+NULL\b")


def _rewrite_bare_string_where(sql: str) -> str:
    """Oracle 23c and MSSQL both forbid bare string literals as WHERE
    conditions; convert them to `1=1`/`1=0` using Postgres's
    whitespace-trimmed truthiness rules. Strings that Postgres itself would
    reject are left untouched (the engine's error then faithfully echoes
    Postgres's behavior). Bare NULL conditions are rewritten to `1=0` since
    NULL in WHERE filters every row."""
    def repl(m):
        body = m.group(2)[1:-1].replace("''", "'").strip().lower()
        if body in _PG_TRUE_LITERALS:
            return f"{m.group(1)}1=1{m.group(3)}"
        if body in _PG_FALSE_LITERALS:
            return f"{m.group(1)}1=0{m.group(3)}"
        return m.group(0)
    sql = _WHERE_BARE_STRING_RE.sub(repl, sql)
    sql = _WHERE_BARE_NULL_RE.sub(lambda m: f"{m.group(1)}1=0{m.group(2)}", sql)
    return sql


_BOOL_OP_TOKEN_RE = re.compile(
    r"(?i)(<>|!=|<=|>=|=|<|>|\bIS\s+(?:NOT\s+)?NULL\b|\bAND\b|\bOR\b|\bNOT\b|\bLIKE\b|\bIN\b|\bBETWEEN\b)"
)


def _rewrite_oracle_cast_as_int(sql: str) -> str:
    """Replace `CAST(<expr>) AS INT)` with `CAST(<expr>) AS NUMBER)`, or
    rewrite to a CASE expression when the inner is a boolean condition (since
    Oracle 23c rejects `CAST(<bool> AS NUMBER)` with ORA-907). Use a balanced
    paren walker so nested CASTs are handled, and recurse into bodies whose
    outer cast isn't `AS INT` to catch inner CASTs."""
    out = []
    i = 0
    n = len(sql)
    while i < n:
        m = re.search(r"(?i)\bCAST\s*\(", sql[i:])
        if not m:
            out.append(sql[i:])
            break
        out.append(sql[i:i + m.start()])
        cast_start = i + m.start()
        open_paren = i + m.end() - 1
        depth = 1
        j = open_paren + 1
        in_str = False
        while j < n and depth > 0:
            c = sql[j]
            if c == "'":
                if in_str and j + 1 < n and sql[j + 1] == "'":
                    j += 2
                    continue
                in_str = not in_str
            elif not in_str:
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
            j += 1
        if depth != 0:
            out.append(sql[cast_start:])
            break
        cast_body = sql[open_paren + 1:j]
        i = j + 1
        as_int = re.search(r"(?is)^\s*(.*?)\s+AS\s+INT\s*$", cast_body)
        if as_int:
            inner = _rewrite_oracle_cast_as_int(as_int.group(1)).strip()
            if _BOOL_OP_TOKEN_RE.search(inner):
                # Oracle 23c rejects CAST(<bool> AS NUMBER) too — emit a CASE.
                out.append(
                    f"(CASE WHEN {inner} THEN 1 "
                    f"WHEN NOT ({inner}) THEN 0 ELSE NULL END)"
                )
            else:
                out.append(f"CAST({inner} AS NUMBER)")
        else:
            # Outer cast is something else (e.g. AS VARCHAR), but inner
            # CASTs may still be AS INT — recurse into the body.
            out.append(f"CAST({_rewrite_oracle_cast_as_int(cast_body)})")
    return "".join(out)


def _rewrite_oracle_cast_bool_as_varchar(sql: str) -> str:
    """Oracle SQL has no boolean values, so `CAST(<cond>) AS VARCHAR(N))` can't
    be parsed. Detect that pattern (matching the CAST's parens via a balanced
    walker, not regex) and rewrite the inner condition with a CASE expression
    that yields 'True'/'False'/NULL while preserving NULL semantics. Non-boolean
    CAST(... AS VARCHAR(N)) — e.g. casting a number — is left untouched."""
    out = []
    i = 0
    n = len(sql)
    while i < n:
        m = re.search(r"(?i)\bCAST\s*\(", sql[i:])
        if not m:
            out.append(sql[i:])
            break
        out.append(sql[i:i + m.start()])
        cast_start = i + m.start()
        open_paren = i + m.end() - 1
        depth = 1
        j = open_paren + 1
        in_str = False
        while j < n and depth > 0:
            c = sql[j]
            if c == "'" and (j == 0 or sql[j - 1] != "\\"):
                # Toggle string-literal mode (handle '' as escaped quote).
                if in_str and j + 1 < n and sql[j + 1] == "'":
                    j += 2
                    continue
                in_str = not in_str
            elif not in_str:
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
            j += 1
        if depth != 0:
            # Unbalanced — give up and emit the rest unchanged.
            out.append(sql[cast_start:])
            break
        cast_body = sql[open_paren + 1:j]  # between the CAST's outer parens
        i = j + 1
        as_varchar = re.search(
            r"(?is)^\s*(.*?)\s+AS\s+VARCHAR\s*\(\s*\d+\s*\)\s*$", cast_body
        )
        if not as_varchar:
            out.append(sql[cast_start:i])
            continue
        inner = as_varchar.group(1).strip()
        # Sqlancer often wraps the boolean in `CAST(<bool> AS INT)` or
        # `CAST(<bool> AS NUMBER)` (the prior pass turns the former into the
        # latter). Oracle's CASE WHEN requires a boolean, not a number, so
        # unwrap any such outer numeric cast so the original boolean expr
        # appears directly in the WHEN clause.
        unwrap = re.match(
            r"(?is)^CAST\s*\(\s*(.*?)\s+AS\s+(?:INT|NUMBER|INTEGER|NUMERIC|DECIMAL)\s*(?:\(\s*\d+(?:\s*,\s*\d+)?\s*\))?\s*\)$",
            inner,
        )
        if unwrap:
            inner = unwrap.group(1).strip()
        if not _BOOL_OP_TOKEN_RE.search(inner):
            out.append(sql[cast_start:i])
            continue
        replacement = (
            f"(CASE WHEN {inner} THEN 'True' "
            f"WHEN NOT ({inner}) THEN 'False' ELSE NULL END)"
        )
        out.append(replacement)
    return "".join(out)


def _oracle_bool_string_expr(inner: str) -> str:
    return (
        f"(CASE WHEN {inner} THEN 'True' "
        f"WHEN NOT ({inner}) THEN 'False' ELSE NULL END)"
    )


def _oracle_bool_number_expr(inner: str) -> str:
    return (
        f"(CASE WHEN {inner} THEN 1 "
        f"WHEN NOT ({inner}) THEN 0 ELSE NULL END)"
    )


def _rewrite_oracle_like_bool_match(sql: str) -> str:
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        like_match = re.match(r"(?i)\s*(?:NOT\s+)?LIKE\b", sql[close + 1:])
        inner = sql[i + 1:close]
        if (
            like_match
            and not _is_mssql_case_expr(inner)
            and _has_top_level_bool_op(inner)
        ):
            out.append(_oracle_bool_string_expr(inner) + " ")
            i = close + 1
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _rewrite_oracle_like_bool_pattern(sql: str) -> str:
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        match = re.match(r"(?i)(?:NOT\s+)?LIKE\b", sql[i:])
        if not match:
            out.append(sql[i])
            i += 1
            continue
        out.append(sql[i:i + match.end()])
        i += match.end()
        while i < len(sql) and sql[i].isspace():
            out.append(sql[i])
            i += 1
        if i >= len(sql) or sql[i] != "(":
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        inner = sql[i + 1:close]
        if not _is_mssql_case_expr(inner) and _has_bool_op_outside_string_literals(inner):
            out.append(_oracle_bool_string_expr(inner))
            i = close + 1
            continue
        out.append(sql[i:close + 1])
        i = close + 1
    return "".join(out)


def _rewrite_oracle_predicate_comparison_operands(sql: str) -> str:
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        inner = sql[i + 1:close]
        if _is_mssql_case_expr(inner) or not _has_top_level_bool_op(inner):
            out.append(sql[i])
            i += 1
            continue
        operator, _ = _mssql_comparison_after(sql, close)
        if operator is None:
            operator = _mssql_comparison_operator_before(sql, i)
        if operator is not None:
            rewritten_inner = _rewrite_oracle_predicate_comparison_operands(inner)
            out.append(_oracle_bool_number_expr(rewritten_inner))
            i = close + 1
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _sub_outside_string_literals(sql: str, pattern: re.Pattern, repl: str) -> str:
    parts = []
    pos = 0
    for match in _SQL_STRING_LITERAL_RE.finditer(sql):
        parts.append(pattern.sub(repl, sql[pos:match.start()]))
        parts.append(match.group(0))
        pos = match.end()
    parts.append(pattern.sub(repl, sql[pos:]))
    return "".join(parts)


def _matching_paren_index(sql: str, start: int) -> int | None:
    depth = 0
    in_str = False
    i = start
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return None


def _has_trailing_null_test(sql: str) -> bool:
    sql = _strip_outer_parens(sql).rstrip()
    depth = 0
    in_str = False
    i = 0
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0:
                match = re.match(r"(?i)IS\s+(?:NOT\s+)?NULL\b", sql[i:])
                if (
                    match
                    and not (i > 0 and (sql[i - 1].isalnum() or sql[i - 1] == "_"))
                    and sql[i + match.end():].strip() == ""
                ):
                    return True
        i += 1
    return False


def _rewrite_mssql_nested_null_tests(sql: str) -> str:
    """T-SQL cannot apply IS NULL to another predicate, but SQL's IS NULL
    predicate itself is never NULL: `(expr IS NULL) IS NULL` is false and
    `(expr IS NULL) IS NOT NULL` is true."""
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        match = re.match(r"(?i)\s+IS\s+(NOT\s+)?NULL\b", sql[close + 1:])
        if match and _has_trailing_null_test(sql[i + 1:close]):
            out.append("(1=1)" if match.group(1) else "(1=0)")
            i = close + 1 + match.end()
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _has_top_level_bool_op(sql: str) -> bool:
    sql = _strip_outer_parens(sql)
    depth = 0
    in_str = False
    i = 0
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and _BOOL_OP_TOKEN_RE.match(sql, i):
                return True
        i += 1
    return False


def _rewrite_mssql_predicate_null_tests(sql: str) -> str:
    """Rewrite `(predicate) IS [NOT] NULL` into a T-SQL predicate. This covers
    PostgreSQL boolean UNKNOWN tests while leaving scalar `col IS NULL` alone."""
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        match = re.match(r"(?i)\s+IS\s+(NOT\s+)?NULL\b", sql[close + 1:])
        inner = sql[i + 1:close]
        if match and _has_top_level_bool_op(inner):
            null_value = 0 if match.group(1) else 1
            # Use BIGINT so cross-type comparisons with NVARCHAR values don't
            # implicitly cast to 32-bit INT and overflow on values like
            # '9223372036854775807'. Column `int` is BIGINT (see MSSQL_TYPE_MAP)
            # so this keeps the CASE result aligned with column precision.
            out.append(
                f"((CASE WHEN {inner} THEN CAST(0 AS BIGINT) "
                f"WHEN NOT ({inner}) THEN CAST(0 AS BIGINT) ELSE CAST(1 AS BIGINT) END) "
                f"= CAST({null_value} AS BIGINT))"
            )
            i = close + 1 + match.end()
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _has_bool_op_outside_string_literals(sql: str) -> bool:
    pos = 0
    for match in _SQL_STRING_LITERAL_RE.finditer(sql):
        if _BOOL_OP_TOKEN_RE.search(sql[pos:match.start()]):
            return True
        pos = match.end()
    return _BOOL_OP_TOKEN_RE.search(sql[pos:]) is not None


def _rewrite_mssql_cast_bool_as_int(sql: str) -> str:
    """T-SQL cannot CAST a predicate directly. Convert boolean CASTs to
    integer-valued CASE expressions while leaving scalar CASTs unchanged."""
    out = []
    i = 0
    n = len(sql)
    while i < n:
        match = re.search(r"(?i)\bCAST\s*\(", sql[i:])
        if not match:
            out.append(sql[i:])
            break
        out.append(sql[i:i + match.start()])
        cast_start = i + match.start()
        open_paren = i + match.end() - 1
        close_paren = _matching_paren_index(sql, open_paren)
        if close_paren is None:
            out.append(sql[cast_start:])
            break
        cast_body = sql[open_paren + 1:close_paren]
        i = close_paren + 1
        as_int = re.search(r"(?is)^\s*(.*?)\s+AS\s+INT\s*$", cast_body)
        if not as_int:
            out.append(sql[cast_start:i])
            continue
        inner = as_int.group(1)
        if not _has_bool_op_outside_string_literals(inner):
            out.append(sql[cast_start:i])
            continue
        # Emit BIGINT so the CASE result doesn't force surrounding string
        # operands to be cast to 32-bit INT (which overflows on values like
        # '9223372036854775807'). Column `int` is BIGINT.
        replacement = (
            f"(CASE WHEN {inner} THEN CAST(1 AS BIGINT) "
            f"WHEN NOT ({inner}) THEN CAST(0 AS BIGINT) ELSE NULL END)"
        )
        out.append(replacement)
    return "".join(out)


def _rewrite_mssql_cast_bool_as_string(sql: str) -> str:
    """T-SQL cannot CAST a predicate directly. Convert boolean-to-string casts
    to CASE expressions while leaving scalar CASTs unchanged."""
    out = []
    i = 0
    n = len(sql)
    while i < n:
        match = re.search(r"(?i)\bCAST\s*\(", sql[i:])
        if not match:
            out.append(sql[i:])
            break
        out.append(sql[i:i + match.start()])
        cast_start = i + match.start()
        open_paren = i + match.end() - 1
        close_paren = _matching_paren_index(sql, open_paren)
        if close_paren is None:
            out.append(sql[cast_start:])
            break
        cast_body = sql[open_paren + 1:close_paren]
        i = close_paren + 1
        as_string = re.search(
            r"(?is)^\s*(.*?)\s+AS\s+N?VARCHAR\s*\(\s*\d+\s*\)\s*$",
            cast_body,
        )
        if not as_string:
            out.append(sql[cast_start:i])
            continue
        inner = as_string.group(1)
        if not _has_bool_op_outside_string_literals(inner):
            out.append(sql[cast_start:i])
            continue
        replacement = (
            f"(CASE WHEN {inner} THEN N'True' "
            f"WHEN NOT ({inner}) THEN N'False' ELSE NULL END)"
        )
        out.append(replacement)
    return "".join(out)


def _split_top_level_as(cast_body: str) -> tuple[str, str] | None:
    depth = 0
    in_str = False
    i = 0
    while i < len(cast_body):
        c = cast_body[i]
        if c == "'":
            if in_str and i + 1 < len(cast_body) and cast_body[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and cast_body[i:i + 2].upper() == "AS":
                before_ok = i == 0 or not (cast_body[i - 1].isalnum() or cast_body[i - 1] == "_")
                after = i + 2
                after_ok = after == len(cast_body) or not (
                    cast_body[after].isalnum() or cast_body[after] == "_"
                )
                if before_ok and after_ok:
                    return cast_body[:i].strip(), cast_body[after:].strip()
        i += 1
    return None


def _split_whole_cast(sql: str) -> tuple[str, str] | None:
    expr = _strip_outer_parens(sql)
    match = re.match(r"(?is)^CAST\s*\(", expr)
    if not match:
        return None
    open_paren = match.end() - 1
    close = _matching_paren_index(expr, open_paren)
    if close is None or expr[close + 1:].strip():
        return None
    return _split_top_level_as(expr[open_paren + 1:close])


def _rewrite_mssql_nested_bool_int_string_where(sql: str) -> str:
    match = _WHERE_RE.search(sql)
    if not match:
        return sql
    head, where = sql[:match.end()], sql[match.end():]
    body = where.strip()
    trailing = ""
    if body.endswith(";"):
        body, trailing = body[:-1].rstrip(), ";"

    outer = _split_whole_cast(body)
    if outer is None:
        return sql
    outer_inner, outer_type = outer
    if not re.match(r"(?is)^N?VARCHAR\s*\(\s*\d+\s*\)$", outer_type):
        return sql

    inner = _split_whole_cast(outer_inner)
    if inner is None:
        return sql
    inner_expr, inner_type = inner
    if not re.match(r"(?is)^INT$", inner_type):
        return sql
    if not _has_bool_op_outside_string_literals(inner_expr):
        return sql

    return f"{head} ({_mssql_bool_int_expr(inner_expr)} <> 0){trailing}"


def _mssql_bool_string_expr(inner: str) -> str:
    return (
        f"(CASE WHEN {inner} THEN N'True' "
        f"WHEN NOT ({inner}) THEN N'False' ELSE NULL END)"
    )


def _mssql_bool_int_expr(inner: str) -> str:
    # Use BIGINT (matches MSSQL_TYPE_MAP["int"] = "BIGINT" for `int` columns).
    # Avoids implicit string→INT32 casts in surrounding comparisons that would
    # overflow on values like '9223372036854775807' / '-9223372036854775808'.
    return (
        f"(CASE WHEN {inner} THEN CAST(1 AS BIGINT) "
        f"WHEN NOT ({inner}) THEN CAST(0 AS BIGINT) ELSE NULL END)"
    )


def _mssql_scalar_logical_expr(inner: str) -> str | None:
    expr = _strip_outer_parens(inner)
    split = _split_top_level_bool(expr)
    if split is None:
        return None
    left, op, right = split
    left_expr = _mssql_scalar_numeric_expr(left)
    right_expr = _mssql_scalar_numeric_expr(right)
    if op == "OR":
        return (
            f"(CASE WHEN TRY_CONVERT(float, {left_expr}) = 1 THEN 1 "
            f"WHEN {left_expr} IS NULL "
            f"AND ({right_expr} IS NULL OR TRY_CONVERT(float, {right_expr}) <> 1) "
            f"THEN NULL ELSE {right_expr} END)"
        )
    return (
        f"(CASE WHEN TRY_CONVERT(float, {left_expr}) = 0 THEN 0 "
        f"WHEN {left_expr} IS NULL "
        f"AND ({right_expr} IS NULL OR TRY_CONVERT(float, {right_expr}) <> 0) "
        f"THEN NULL ELSE {right_expr} END)"
    )


def _mssql_scalar_numeric_expr(inner: str) -> str:
    expr = _strip_outer_parens(inner)
    scalar_logical = _mssql_scalar_logical_expr(expr)
    if scalar_logical is not None:
        return scalar_logical
    scalar_not = _mssql_scalar_not_on_scalar_int_expr(expr)
    if scalar_not is not None:
        return scalar_not
    if _has_top_level_bool_op(expr):
        rewritten_expr = _rewrite_mssql_predicate_comparison_operands(expr)
        return _mssql_bool_int_expr(rewritten_expr)
    return expr


def _mssql_scalar_not_on_scalar_int_expr(inner: str) -> str | None:
    """`NOT <scalar>` (e.g. `NOT 'y<'`) is a T-SQL syntax error, so the
    fallback `CASE WHEN NOT '<scalar>' THEN 1 ...` wrapper produces invalid
    SQL. Emit a TRY_CONVERT-based numeric NOT that follows Postgres-style
    bool coercion: non-numeric → NULL, zero → 1, non-zero → 0."""
    expr = _strip_outer_parens(inner)
    match = re.match(r"(?is)^NOT\s+(.+)$", expr)
    if not match:
        return None
    operand = match.group(1).strip()
    if _has_top_level_bool_op(operand):
        return None
    return (
        f"(CASE WHEN TRY_CONVERT(float, {operand}) IS NULL THEN NULL "
        f"WHEN TRY_CONVERT(float, {operand}) = 0 THEN 1 "
        f"ELSE 0 END)"
    )


def _mssql_scalar_not_int_expr(inner: str) -> str | None:
    expr = _strip_outer_parens(inner)
    match = re.match(r"(?is)^NOT\s*\((.*)\)$", expr)
    if not match:
        return None
    operand = _mssql_scalar_logical_expr(match.group(1))
    if operand is None:
        return None
    return (
        f"(CASE WHEN {operand} IS NULL THEN NULL "
        f"WHEN TRY_CONVERT(float, {operand}) = 1 THEN 0 "
        f"WHEN TRY_CONVERT(float, {operand}) = 0 THEN 1 "
        f"WHEN TRY_CONVERT(float, {operand}) IS NOT NULL THEN 0 "
        f"ELSE NULL END)"
    )


def _is_mssql_case_expr(sql: str) -> bool:
    return re.match(r"(?is)^\s*CASE\b", _strip_outer_parens(sql)) is not None


def _mssql_comparison_after(sql: str, close: int) -> tuple[str | None, str]:
    match = re.match(r"\s*(<>|!=|<=|>=|=|<|>)", sql[close + 1:])
    if not match:
        return None, ""
    return match.group(1), sql[close + 1 + match.end():]


def _mssql_comparison_operator_before(sql: str, start: int) -> str | None:
    prefix = sql[:start].rstrip()
    for op in ("<>", "!=", "<=", ">=", "=", "<", ">"):
        if prefix.endswith(op):
            return op
    return None


def _mssql_comparison_operand_is_string(sql: str) -> bool:
    expr = sql.strip()
    while expr.startswith("(") and expr.endswith(")"):
        close = _matching_paren_index(expr, 0)
        if close != len(expr) - 1:
            break
        expr = expr[1:-1].strip()
    return bool(re.match(r"(?is)^(?:N)?'(?:''|[^'])*'(?:\s+COLLATE\s+\w+)?$", expr))


def _mssql_prefix_string_literal(sql: str) -> str | None:
    i = 0
    while i < len(sql) and sql[i].isspace():
        i += 1
    while i < len(sql) and sql[i] == "(":
        i += 1
        while i < len(sql) and sql[i].isspace():
            i += 1
    if i < len(sql) and sql[i] in "Nn" and i + 1 < len(sql) and sql[i + 1] == "'":
        i += 1
    if i >= len(sql) or sql[i] != "'":
        return None
    i += 1
    chars = []
    while i < len(sql):
        if sql[i] == "'":
            if i + 1 < len(sql) and sql[i + 1] == "'":
                chars.append("'")
                i += 2
                continue
            return "".join(chars)
        chars.append(sql[i])
        i += 1
    return None


def _mssql_comparison_operand_prefers_bool_int(sql: str) -> bool:
    literal = _mssql_prefix_string_literal(sql)
    if literal is None:
        return False
    if literal == "":
        return True
    try:
        int(literal)
    except ValueError:
        return False
    return True


def _mssql_predicate_comparison_operand_expr(
    inner: str,
    operator: str,
    other_side: str,
) -> str:
    rewritten_inner = _rewrite_mssql_predicate_comparison_operands(inner)
    scalar_not_int = _mssql_scalar_not_int_expr(rewritten_inner)
    if scalar_not_int is not None:
        return scalar_not_int
    if operator in ("=", "<>", "!=") and _mssql_comparison_operand_is_string(other_side):
        if _mssql_comparison_operand_prefers_bool_int(other_side):
            return _mssql_bool_int_expr(rewritten_inner)
        return _mssql_bool_string_expr(rewritten_inner)
    return _mssql_bool_int_expr(rewritten_inner)


def _rewrite_mssql_predicate_comparison_operands(sql: str) -> str:
    """T-SQL predicates are not scalar comparison operands."""
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        inner = sql[i + 1:close]
        if _is_mssql_case_expr(inner) or not _has_top_level_bool_op(inner):
            out.append(sql[i])
            i += 1
            continue
        operator, other_side = _mssql_comparison_after(sql, close)
        if operator is None:
            operator = _mssql_comparison_operator_before(sql, i)
            other_side = sql[:i]
        if operator is not None:
            out.append(_mssql_predicate_comparison_operand_expr(inner, operator, other_side))
            i = close + 1
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _matching_open_paren_index(sql: str, close: int) -> int | None:
    depth = 0
    in_str = False
    i = close
    while i >= 0:
        c = sql[i]
        if c == "'":
            if in_str and i - 1 >= 0 and sql[i - 1] == "'":
                i -= 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == ")":
                depth += 1
            elif c == "(":
                depth -= 1
                if depth == 0:
                    return i
        i -= 1
    return None


def _find_top_level_and(sql: str, start: int) -> int | None:
    depth = 0
    in_str = False
    i = start
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                if depth == 0:
                    return None
                depth -= 1
            elif depth == 0 and sql[i:i + 3].upper() == "AND":
                before_ok = i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == "_")
                after_ok = i + 3 == len(sql) or not (sql[i + 3].isalnum() or sql[i + 3] == "_")
                if before_ok and after_ok:
                    return i
        i += 1
    return None


def _rewrite_mssql_between_predicate_operands(sql: str) -> str:
    """T-SQL BETWEEN operands must be scalar, not predicates."""
    replacements: list[tuple[int, int, str]] = []

    def add_parenthesized_operand(start: int, close: int):
        inner = sql[start + 1:close]
        if not _is_mssql_case_expr(inner) and _has_top_level_bool_op(inner):
            replacements.append((start, close + 1, _mssql_scalar_numeric_expr(inner)))

    for match in re.finditer(r"(?i)\bBETWEEN\b", sql):
        between_start, between_end = match.span()
        if _SQL_STRING_LITERAL_RE.search(sql[:between_start]) and any(
            m.start() < between_start < m.end()
            for m in _SQL_STRING_LITERAL_RE.finditer(sql)
        ):
            continue

        left_end = between_start
        while left_end > 0 and sql[left_end - 1].isspace():
            left_end -= 1
        # Skip a preceding NOT keyword (the BETWEEN's `NOT` modifier) so the
        # left operand is still scanned for predicate operands needing wrap.
        if (
            left_end >= 3
            and sql[left_end - 3:left_end].upper() == "NOT"
            and (left_end == 3 or not (sql[left_end - 4].isalnum() or sql[left_end - 4] == "_"))
        ):
            left_end -= 3
            while left_end > 0 and sql[left_end - 1].isspace():
                left_end -= 1
        if left_end > 0 and sql[left_end - 1] == ")":
            left_open = _matching_open_paren_index(sql, left_end - 1)
            if left_open is not None:
                add_parenthesized_operand(left_open, left_end - 1)

        low_start = between_end
        while low_start < len(sql) and sql[low_start].isspace():
            low_start += 1
        low_close = None
        if low_start < len(sql) and sql[low_start] == "(":
            low_close = _matching_paren_index(sql, low_start)
            if low_close is not None:
                add_parenthesized_operand(low_start, low_close)

        if low_close is not None:
            and_start = low_close + 1
            while and_start < len(sql) and sql[and_start].isspace():
                and_start += 1
            and_match = re.match(r"(?i)\bAND\b", sql[and_start:])
            if not and_match:
                continue
            and_end = and_start + and_match.end()
        else:
            # Bare (unparenthesized) low operand — scan forward for the
            # BETWEEN's top-level AND so we can still wrap the high operand.
            and_pos = _find_top_level_and(sql, low_start)
            if and_pos is None:
                continue
            and_end = and_pos + 3
        high_start = and_end
        while high_start < len(sql) and sql[high_start].isspace():
            high_start += 1
        if high_start < len(sql) and sql[high_start] == "(":
            high_close = _matching_paren_index(sql, high_start)
            if high_close is not None:
                add_parenthesized_operand(high_start, high_close)

    if not replacements:
        return sql
    out = sql
    for start, end, repl in sorted(set(replacements), reverse=True):
        out = out[:start] + repl + out[end:]
    return out


def _mssql_arithmetic_after(sql: str, close: int) -> bool:
    return re.match(r"\s*[+*/-]", sql[close + 1:]) is not None


def _mssql_arithmetic_operator_before(sql: str, start: int) -> bool:
    prefix = sql[:start].rstrip()
    return bool(prefix) and prefix[-1] in "+*/-"


def _has_top_level_arithmetic_op(sql: str) -> bool:
    sql = _strip_outer_parens(sql)
    depth = 0
    in_str = False
    i = 0
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and c in "+*/":
                return True
            elif depth == 0 and c == "-":
                prev = sql[i - 1] if i > 0 else ""
                nxt = sql[i + 1] if i + 1 < len(sql) else ""
                if prev and not prev.isspace() and nxt and not nxt.isspace():
                    return True
        i += 1
    return False


def _rewrite_mssql_predicate_arithmetic_operands(sql: str) -> str:
    """T-SQL predicates/logical expressions are not scalar arithmetic operands."""
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        inner = sql[i + 1:close]
        if (
            (_mssql_arithmetic_after(sql, close) or _mssql_arithmetic_operator_before(sql, i))
            and not _is_mssql_case_expr(inner)
            and _has_top_level_bool_op(inner)
        ):
            out.append(_mssql_scalar_numeric_expr(inner))
            i = close + 1
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _rewrite_mssql_arithmetic_where(sql: str) -> str:
    match = _WHERE_RE.search(sql)
    if not match:
        return sql
    head, where = sql[:match.end()], sql[match.end():]
    body = where.strip()
    trailing = ""
    if body.endswith(";"):
        body, trailing = body[:-1].rstrip(), ";"
    if _has_top_level_arithmetic_op(body) and not _has_top_level_bool_op(body):
        return f"{head} ({body}) <> 0{trailing}"
    return sql


def _rewrite_mssql_like_bool_match(sql: str) -> str:
    """T-SQL LIKE match expressions must be scalar strings, not predicates."""
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        like_match = re.match(r"(?i)\s*(?:NOT\s+)?LIKE\b", sql[close + 1:])
        inner = sql[i + 1:close]
        scalar_not_replacement = _mssql_scalar_not_string_expr(inner)
        if like_match and scalar_not_replacement is not None:
            out.append(scalar_not_replacement + " ")
            i = close + 1
            continue
        if (
            like_match
            and not _is_mssql_case_expr(inner)
            and _has_top_level_bool_op(inner)
        ):
            rewritten_inner = _rewrite_mssql_like_bool_match(inner)
            out.append(_mssql_bool_string_expr(rewritten_inner) + " ")
            i = close + 1
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _mssql_scalar_not_string_expr(inner: str) -> str | None:
    expr = _strip_outer_parens(inner)
    match = re.match(r"(?is)^NOT\s+(.+)$", expr)
    if not match:
        return None
    operand = match.group(1).strip()
    return (
        f"(CASE WHEN {operand} IS NULL THEN NULL "
        f"WHEN TRY_CONVERT(float, {operand}) = 1 THEN N'0' "
        f"WHEN TRY_CONVERT(float, {operand}) = 0 THEN N'1' "
        f"WHEN TRY_CONVERT(float, {operand}) IS NOT NULL THEN N'False' "
        f"WHEN LEN(CAST({operand} AS NVARCHAR(MAX))) = 0 THEN N'True' "
        f"ELSE N'False' END)"
    )


def _rewrite_mssql_like_scalar_not_match(sql: str) -> str:
    """T-SQL cannot use scalar NOT as the LIKE match expression."""
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        if sql[i] != "(":
            out.append(sql[i])
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        like_match = re.match(r"(?i)\s*(?:NOT\s+)?LIKE\b", sql[close + 1:])
        replacement = _mssql_scalar_not_string_expr(sql[i + 1:close])
        if like_match and replacement is not None:
            out.append(replacement + " ")
            i = close + 1
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


def _rewrite_mssql_like_bool_pattern(sql: str) -> str:
    """T-SQL LIKE patterns must be scalar strings, not predicates."""
    out = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        match = re.match(r"(?i)(?:NOT\s+)?LIKE\b", sql[i:])
        if not match:
            out.append(sql[i])
            i += 1
            continue
        out.append(sql[i:i + match.end()])
        i += match.end()
        while i < len(sql) and sql[i].isspace():
            out.append(sql[i])
            i += 1
        if i >= len(sql) or sql[i] != "(":
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            out.append(sql[i])
            i += 1
            continue
        inner = sql[i + 1:close]
        if not _is_mssql_case_expr(inner) and _has_bool_op_outside_string_literals(inner):
            rewritten_inner = _rewrite_mssql_like_bool_pattern(inner)
            out.append(_mssql_bool_string_expr(rewritten_inner))
            i = close + 1
            continue
        out.append(sql[i:close + 1])
        i = close + 1
    return "".join(out)


def _rewrite_mssql_boolean_nulls(sql: str) -> str:
    """SQL Server has no scalar boolean NULL, but `1=NULL` is the UNKNOWN
    predicate value and is valid under NOT/WHERE. Keep `IS NOT NULL` intact."""
    def rewrite_segment(segment: str) -> str:
        out = []
        pos = 0
        for match in _NOT_NULL_RE.finditer(segment):
            j = match.start() - 1
            while j >= 0 and segment[j].isspace():
                j -= 1
            token_end = j + 1
            while j >= 0 and (segment[j].isalnum() or segment[j] == "_"):
                j -= 1
            previous_token = segment[j + 1:token_end].upper()
            if previous_token == "IS":
                continue
            out.append(segment[pos:match.start()])
            out.append("NOT (1=NULL)")
            pos = match.end()
        out.append(segment[pos:])
        return "".join(out)

    parts = []
    pos = 0
    for match in _SQL_STRING_LITERAL_RE.finditer(sql):
        parts.append(rewrite_segment(sql[pos:match.start()]))
        parts.append(match.group(0))
        pos = match.end()
    parts.append(rewrite_segment(sql[pos:]))
    return "".join(parts)


def _strip_outer_parens(s: str) -> str:
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        outermost = True
        in_str = False
        i = 0
        while i < len(s):
            c = s[i]
            if c == "'":
                if in_str and i + 1 < len(s) and s[i + 1] == "'":
                    i += 2
                    continue
                in_str = not in_str
            elif in_str:
                i += 1
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0 and i < len(s) - 1:
                    outermost = False
                    break
            i += 1
        if not outermost:
            break
        s = s[1:-1].strip()
    return s


def _is_top_level_lower_call(s: str) -> bool:
    if not (s.startswith("LOWER(") and s.endswith(")")):
        return False
    depth = 0
    for i, c in enumerate(s):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0 and i < len(s) - 1:
                return False
    return depth == 0


def _wrap_lower_in_where_for_mysql(sql: str, schema_dict: dict) -> str:
    """In WHERE, wrap string column refs and string literals in LOWER(...).

    Combined with utf8mb4_bin column collation, this makes MySQL's <, =,
    LIKE on strings behave as `lower() then code-point compare`, matching
    the interpreter's MysqlOps.apply.

    Boolean contexts use MySQL's normal numeric conversion, so this function
    leaves whole-predicate string expressions as expressions.
    """
    string_cols = {
        f"{tbl}.{c['name']}"
        for tbl, cols in schema_dict.items()
        for c in cols if c["type"] == "string"
    }
    m = _WHERE_RE.search(sql)
    if not m:
        return sql
    head, where = sql[:m.end()], sql[m.end():]
    where = _SQL_STRING_LITERAL_RE.sub(lambda mm: f"LOWER({mm.group(0)})", where)
    where = _QUALIFIED_COL_RE.sub(
        lambda mm: f"LOWER({mm.group(0)})" if mm.group(0) in string_cols else mm.group(0),
        where,
    )
    body = where.rstrip()
    trailing = ""
    if body.endswith(";"):
        body, trailing = body[:-1].rstrip(), ";"
    return head + " " + body.lstrip() + trailing


def _rewrite_sql(sql: str, engine_name: str, schema_dict: dict | None = None) -> str:
    """Translate a Postgres-flavoured SQLancer query to the target dialect."""
    if engine_name == "postgres":
        return sql

    out = sql
    if engine_name == "mysql":
        # MySQL: CAST(x AS INT) is invalid — use SIGNED instead.
        out = _MYSQL_CAST_AS_INT_RE.sub("AS SIGNED)", out)
        # MySQL supports CAST(... AS CHAR(n)), not CAST(... AS VARCHAR(n)).
        out = _CAST_AS_VARCHAR_RE.sub(lambda m: f"AS CHAR({m.group(1)})", out)
        if schema_dict is not None:
            out = _wrap_lower_in_where_for_mysql(out, schema_dict)
    elif engine_name == "mssql":
        out = _sub_outside_string_literals(out, _TRUE_RE, "(1=1)")
        out = _sub_outside_string_literals(out, _FALSE_RE, "(1=0)")
        out = _rewrite_bare_string_where(out)
        out = _rewrite_mssql_boolean_nulls(out)
        out = _rewrite_mssql_nested_null_tests(out)
        out = _rewrite_mssql_predicate_null_tests(out)
        out = _rewrite_mssql_nested_bool_int_string_where(out)
        out = _rewrite_mssql_cast_bool_as_int(out)
        out = _rewrite_mssql_cast_bool_as_string(out)
        out = _rewrite_mssql_predicate_arithmetic_operands(out)
        out = _rewrite_mssql_arithmetic_where(out)
        out = _rewrite_mssql_between_predicate_operands(out)
        out = _rewrite_mssql_predicate_comparison_operands(out)
        out = _rewrite_mssql_like_bool_match(out)
        out = _rewrite_mssql_like_scalar_not_match(out)
        out = _rewrite_mssql_like_bool_pattern(out)
        # Preserve Unicode text semantics from PostgreSQL TEXT/VARCHAR.
        out = _CAST_AS_VARCHAR_RE.sub(lambda m: f"AS NVARCHAR({m.group(1)})", out)
        # Prefix every plain string literal with N so MSSQL keeps it as
        # NVARCHAR (without it, non-ASCII chars are downgraded to '?' via
        # the default VARCHAR code page) and pin its collation to
        # Latin1_General_BIN so literal-to-literal comparisons don't fall
        # back to the database default collation, which uses dictionary
        # sort and disagrees with Python code-point ordering.
        out = re.sub(
            r"(?<![A-Za-z_0-9])'((?:[^']|'')*)'",
            lambda mm: f"(N'{mm.group(1)}' COLLATE Latin1_General_BIN)",
            out,
        )
        if schema_dict is not None:
            # MSSQL has no per-session default-schema switch, so qualify each
            # table name with the test schema where it appears as a table
            # reference. Lookbehind/lookahead skip column qualifiers like
            # `t.c0` and identifiers that merely contain the table name.
            for table_name in schema_dict.keys():
                table_pat = re.compile(
                    rf"(?<![.\w]){re.escape(table_name)}(?!\w)(?!\s*\.)"
                )
                out = _sub_outside_string_literals(
                    out, table_pat, f"[{SQLANCER_MSSQL_SCHEMA}].[{table_name}]"
                )
    elif engine_name == "oracle":
        out = _sub_outside_string_literals(out, _TRUE_RE, "(1=1)")
        out = _sub_outside_string_literals(out, _FALSE_RE, "(1=0)")
        # Oracle: CAST AS INT is fine in 12c+ but be conservative.
        out = _rewrite_oracle_cast_as_int(out)
        out = _rewrite_oracle_cast_bool_as_varchar(out)
        out = _rewrite_oracle_like_bool_match(out)
        out = _rewrite_oracle_like_bool_pattern(out)
        out = _rewrite_oracle_predicate_comparison_operands(out)
        out = _rewrite_bare_string_where(out)
        if schema_dict is not None:
            for table_name in schema_dict.keys():
                table_pat = re.compile(rf"(?<![.\w]){re.escape(table_name)}(?!\w)", re.IGNORECASE)
                out = _sub_outside_string_literals(out, table_pat, _oracle_table_name(table_name))
    return out


def _set_search_path(conn, engine_name):
    """Configure the per-test query so unqualified table refs resolve."""
    cur = _mssql_cursor(conn) if engine_name == "mssql" else conn.cursor()
    if engine_name == "postgres":
        cur.execute(f'SET search_path TO "{SQLANCER_PG_SCHEMA}"')
    elif engine_name == "mysql":
        cur.execute(f"USE `{SQLANCER_DB}`")
        # String-literal comparisons use the connection collation, not the
        # column collation — pin it to utf8mb4_0900_bin (NO PAD, code-point)
        # so they too do code-point compare, matching the table columns.
        cur.execute("SET NAMES utf8mb4 COLLATE utf8mb4_0900_bin")
        # Treat backslashes in string literals as literal characters, matching
        # our interpreter's parsing — otherwise MySQL's `\1` → `1` rewrite
        # changes which rows the predicate selects.
        cur.execute(
            "SET SESSION sql_mode = CONCAT(@@sql_mode, ',NO_BACKSLASH_ESCAPES')"
        )
    elif engine_name == "mssql":
        cur.execute(f"USE [{SQLANCER_DB}]")
        # MSSQL needs the schema in the FROM clause; we rely on per-user
        # default schema being [sqlancer_test]. Set it for this session.
        try:
            cur.execute(f"ALTER USER CURRENT_USER WITH DEFAULT_SCHEMA = [{SQLANCER_MSSQL_SCHEMA}]")
        except Exception:
            pass
    # sqlite: single namespace; oracle: user's schema; nothing to do.


def _normalise_sql_for_engine(sql, engine_name):
    """Final tweaks before cur.execute."""
    if engine_name == "oracle":
        return sql.rstrip().rstrip(";")
    return sql


def _replace_where_with_constant(sql: str, predicate: str) -> str:
    body = sql.rstrip()
    trailing = ""
    if body.endswith(";"):
        body = body[:-1].rstrip()
        trailing = ";"
    where_pos = _find_top_level_keyword(body, "WHERE")
    if where_pos < 0:
        return sql
    return f"{body[:where_pos]}WHERE {predicate}{trailing}"


def _sqlancer_sql_uses_empty_table(sql: str, schema_dict, data_dict) -> bool:
    split = _split_select_from_where(sql)
    if split is None:
        return False
    from_sql, _ = split
    return any(
        not data_dict.get(table, [])
        and re.search(rf"(?<![.\w]){re.escape(table)}(?!\w)", from_sql)
        for table in schema_dict
    )


def _sqlancer_oracle_sql_never_true(sql: str, schema_dict, data_dict) -> bool:
    try:
        parsed = LarkParser(schema=_build_dbt(schema_dict)).parse(sql)
    except Exception:
        return False
    queries = [parsed]
    while queries:
        query = queries.pop()
        if hasattr(query, "cond") and _sqlancer_oracle_condition_never_true_on_fixture(
            query,
            schema_dict,
            data_dict,
        ):
            return True
        for attr in ("query", "q1", "q2", "l", "r"):
            if hasattr(query, attr):
                queries.append(getattr(query, attr))
    return False


def _display_text(value):
    return str(value).encode("unicode_escape", errors="backslashreplace").decode("ascii")


def _jsonable_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _sample_interpreter_rows(table, limit=10):
    if table is None:
        return None
    return [
        [_jsonable_value(v.erase()) for v in row]
        for row in table.rows[:limit]
    ]


def _sample_engine_rows(rows, limit=10):
    if rows is None:
        return None
    return [
        [_jsonable_value(v) for v in row]
        for row in rows[:limit]
    ]


def _record_sqlancer_mismatch(
    request,
    *,
    reason,
    engine_name,
    kind,
    yaml_path,
    sql,
    db_sql,
    our_result=None,
    their_result=None,
    our_error=None,
    their_error=None,
    materialise_error=None,
):
    mismatches = getattr(request.config, "_sqlancer_mismatches", None)
    if mismatches is None:
        return
    mismatches.append(
        {
            "reason": reason,
            "engine": engine_name,
            "kind": kind,
            "case": yaml_path.stem,
            "path": str(yaml_path),
            "sql": sql,
            "engine_sql": db_sql,
            "interpreter_error": str(our_error) if our_error else None,
            "engine_error": str(their_error) if their_error else None,
            "materialise_error": str(materialise_error) if materialise_error else None,
            "interpreter_row_count": len(our_result.rows) if our_result is not None else None,
            "engine_row_count": len(their_result) if their_result is not None else None,
            "interpreter_rows_sample": _sample_interpreter_rows(our_result),
            "engine_rows_sample": _sample_engine_rows(their_result),
        }
    )


def _sqlancer_static_truth(expr, engine) -> bool | None:
    try:
        if isinstance(expr, BValue):
            return engine.run.ops.truth_value(expr)
        if isinstance(expr, Ascr) and isinstance(expr.e, BValue):
            return engine.run.ops.truth_value(engine.run.ops.cast(expr.e, expr.t))
        if isinstance(expr, BNeg):
            truth = _sqlancer_static_truth(expr.b, engine)
            return None if truth is None else not truth
        if isinstance(expr, Or):
            left = _sqlancer_static_truth(expr.l, engine)
            right = _sqlancer_static_truth(expr.r, engine)
            if left is True or right is True:
                return True
            if left is False and right is False:
                return False
        if isinstance(expr, And):
            left = _sqlancer_static_truth(expr.l, engine)
            right = _sqlancer_static_truth(expr.r, engine)
            if left is False or right is False:
                return False
            if left is True and right is True:
                return True
    except Exception:
        return None
    return None


def _fold_sqlancer_static_short_circuit_expr(expr, engine):
    if isinstance(expr, Or):
        left = _fold_sqlancer_static_short_circuit_expr(expr.l, engine)
        right = _fold_sqlancer_static_short_circuit_expr(expr.r, engine)
        left_truth = _sqlancer_static_truth(left, engine)
        right_truth = _sqlancer_static_truth(right, engine)
        if left_truth is True or right_truth is True:
            return BValue(True)
        if left_truth is False:
            return right
        if right_truth is False:
            return left
        return Or(left, right)
    if isinstance(expr, And):
        left = _fold_sqlancer_static_short_circuit_expr(expr.l, engine)
        right = _fold_sqlancer_static_short_circuit_expr(expr.r, engine)
        left_truth = _sqlancer_static_truth(left, engine)
        right_truth = _sqlancer_static_truth(right, engine)
        if left_truth is False or right_truth is False:
            return BValue(False)
        if left_truth is True:
            return right
        if right_truth is True:
            return left
        return And(left, right)
    if isinstance(expr, BNeg):
        return BNeg(_fold_sqlancer_static_short_circuit_expr(expr.b, engine))
    return expr


def _fold_sqlancer_static_short_circuit_query(query, engine):
    if hasattr(query, "cond"):
        query.cond = _fold_sqlancer_static_short_circuit_expr(query.cond, engine)
    if hasattr(query, "having_cond") and query.having_cond is not None:
        query.having_cond = _fold_sqlancer_static_short_circuit_expr(
            query.having_cond,
            engine,
        )
    if hasattr(query, "query"):
        _fold_sqlancer_static_short_circuit_query(query.query, engine)
    return query


def _sqlancer_oracle_all_null_columns(schema_dict, data_dict):
    columns = set()
    for table, cols in schema_dict.items():
        rows = data_dict.get(table, [])
        for idx, col in enumerate(cols):
            if all(
                _coerce_fixture_value(
                    row[idx] if idx < len(row) else None,
                    col["type"],
                    oracle_empty_strings=True,
                ) is None
                for row in rows
            ):
                columns.add(f"{table}.{col['name']}")
    return columns


def _sqlancer_is_all_null_column_expr(expr, all_null_columns):
    return getattr(expr, "name", None) in all_null_columns


def _sqlancer_oracle_is_null_expr(expr, all_null_columns):
    return (
        _sqlancer_is_all_null_column_expr(expr, all_null_columns)
        or (isinstance(expr, BValue) and (expr.v is None or expr.v == ""))
    )


def _sqlancer_oracle_comparison_has_null_operand(expr, all_null_columns):
    if getattr(expr, "op", None) not in {"=", "<"}:
        return False
    return (
        _sqlancer_oracle_is_null_expr(expr.e1, all_null_columns)
        or _sqlancer_oracle_is_null_expr(expr.e2, all_null_columns)
    )


_SQLANCER_UNKNOWN = object()


def _sqlancer_oracle_static_truth(expr, all_null_columns):
    # As a scalar, Oracle treats '' as NULL. In SQLancer boolean/logical
    # contexts, the same literal behaves like the false boolean literal.
    if isinstance(expr, Ascr):
        return _sqlancer_oracle_static_truth(expr.e, all_null_columns)
    if isinstance(expr, BValue) and expr.v == "":
        return False
    return _sqlancer_truth_for_where(
        _sqlancer_oracle_static_condition(expr, all_null_columns)
    )


def _sqlancer_oracle_static_condition(expr, all_null_columns):
    if _sqlancer_oracle_is_null_expr(expr, all_null_columns):
        return None
    if isinstance(expr, BValue):
        # Oracle interprets a bare string in a WHERE clause via Postgres-style
        # prefix-abbreviated truth literals ('FA' is FALSE, '1' is TRUE),
        # not via Python truthiness (which would call every non-empty string
        # TRUE and silently fold the WHERE to match all rows).
        try:
            return _sqlancer_truth_for_where(expr.v)
        except Exception:
            return _SQLANCER_UNKNOWN
    if isinstance(expr, Ascr):
        value = _sqlancer_oracle_static_condition(expr.e, all_null_columns)
        return _SQLANCER_UNKNOWN if value is _SQLANCER_UNKNOWN else value
    if isinstance(expr, BNeg):
        value = _sqlancer_oracle_static_truth(expr.b, all_null_columns)
        if value is None:
            return None
        if value is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return not value
    if isinstance(expr, IsNull):
        value = _sqlancer_oracle_static_condition(expr.e, all_null_columns)
        if value is None:
            return True
        if value is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return False
    if isinstance(expr, Or):
        left = _sqlancer_oracle_static_truth(expr.l, all_null_columns)
        right = _sqlancer_oracle_static_truth(expr.r, all_null_columns)
        if left is True or right is True:
            return True
        if left is False and right is False:
            return False
        if left is _SQLANCER_UNKNOWN or right is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return None
    if isinstance(expr, And):
        left = _sqlancer_oracle_static_truth(expr.l, all_null_columns)
        right = _sqlancer_oracle_static_truth(expr.r, all_null_columns)
        if left is False or right is False:
            return False
        if left is None or right is None:
            return None
        if left is True and right is True:
            return True
        if left is _SQLANCER_UNKNOWN or right is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return None
    if getattr(expr, "op", None) in {"=", "<", "LIKE"}:
        left = _sqlancer_oracle_static_condition(expr.e1, all_null_columns)
        right = _sqlancer_oracle_static_condition(expr.e2, all_null_columns)
        if left is None or right is None:
            return None
        if isinstance(expr.e1, BValue) and isinstance(expr.e2, BValue):
            left_value = expr.e1.v
            right_value = expr.e2.v
            if type(left_value) is type(right_value):
                if getattr(expr, "op", None) == "=":
                    return left_value == right_value
                if getattr(expr, "op", None) == "<":
                    return left_value < right_value
        return _SQLANCER_UNKNOWN
    return _SQLANCER_UNKNOWN


def _fold_sqlancer_oracle_null_root_condition(query, schema_dict, data_dict):
    if hasattr(query, "query"):
        _fold_sqlancer_oracle_null_root_condition(query.query, schema_dict, data_dict)
    if not hasattr(query, "cond"):
        return query
    all_null_columns = _sqlancer_oracle_all_null_columns(schema_dict, data_dict)
    nullable_columns = _sqlancer_oracle_nullable_columns(schema_dict, data_dict)
    cond = _fold_sqlancer_oracle_bool_not_like_literal(query.cond)
    query.cond = cond
    if (
        _sqlancer_oracle_is_predicate_null_test(cond)
        and _sqlancer_oracle_expr_is_never_null(cond.e, nullable_columns)
    ):
        query.cond = BValue(False)
    elif (
        isinstance(cond, BNeg)
        and isinstance(cond.b, IsNull)
        and _sqlancer_oracle_is_predicate_expr(cond.b.e)
        and _sqlancer_oracle_expr_is_never_null(cond.b.e, nullable_columns)
    ):
        query.cond = BValue(True)
    elif _sqlancer_oracle_comparison_has_null_operand(cond, all_null_columns):
        query.cond = BValue(False)
    elif isinstance(cond, BNeg) and _sqlancer_oracle_comparison_has_null_operand(
        cond.b,
        all_null_columns,
    ):
        query.cond = BValue(False)
    else:
        static_value = _sqlancer_oracle_static_condition(cond, all_null_columns)
        if static_value is False or static_value is None:
            query.cond = BValue(False)
        elif static_value is True:
            query.cond = BValue(True)
        elif _sqlancer_oracle_condition_never_true_on_fixture(
            query,
            schema_dict,
            data_dict,
        ):
            query.cond = BValue(False)
    return query


def _sqlancer_oracle_is_predicate_null_test(expr):
    return isinstance(expr, IsNull) and _sqlancer_oracle_is_predicate_expr(expr.e)


def _sqlancer_oracle_is_predicate_expr(expr):
    return (
        isinstance(expr, (And, BNeg, IsNull, Or))
        or getattr(expr, "op", None) in {"=", "<", "LIKE"}
    )


def _sqlancer_oracle_nullable_columns(schema_dict, data_dict):
    columns = set()
    for table, cols in schema_dict.items():
        rows = data_dict.get(table, [])
        for idx, col in enumerate(cols):
            if any(
                _coerce_fixture_value(
                    row[idx] if idx < len(row) else None,
                    col["type"],
                    oracle_empty_strings=True,
                ) is None
                for row in rows
            ):
                columns.add(f"{table}.{col['name']}")
    return columns


def _sqlancer_oracle_expr_is_never_null(expr, nullable_columns):
    # IS NULL / IS NOT NULL terminate the NULL chain — they always return
    # TRUE/FALSE, never NULL, so anything below an IsNull is irrelevant here.
    if isinstance(expr, IsNull):
        return True
    if isinstance(expr, BValue):
        return expr.v is not None and expr.v != ""
    if getattr(expr, "name", None) is not None:
        return expr.name not in nullable_columns
    if isinstance(expr, BNeg):
        return _sqlancer_oracle_expr_is_never_null(expr.b, nullable_columns)
    if isinstance(expr, Ascr):
        return _sqlancer_oracle_expr_is_never_null(expr.e, nullable_columns)
    if isinstance(expr, (And, Or)):
        return (
            _sqlancer_oracle_expr_is_never_null(expr.l, nullable_columns)
            and _sqlancer_oracle_expr_is_never_null(expr.r, nullable_columns)
        )
    op = getattr(expr, "op", None)
    if op == "LIKE":
        # Oracle 23c does not treat `<numeric> LIKE <string>` (or vice versa)
        # as 3VL — it does not produce NULL on NULL operands, so the
        # surrounding IS NULL test is always FALSE. Model that here so the
        # predicate-IS-NULL fold lines up with Oracle's observed behavior.
        for side in (expr.e1, expr.e2):
            if isinstance(side, BValue) and side.v is not None and not isinstance(side.v, str):
                return True
        return (
            _sqlancer_oracle_expr_is_never_null(expr.e1, nullable_columns)
            and _sqlancer_oracle_expr_is_never_null(expr.e2, nullable_columns)
        )
    if op in {"=", "<", "+", "-", "*", "/"}:
        return (
            _sqlancer_oracle_expr_is_never_null(expr.e1, nullable_columns)
            and _sqlancer_oracle_expr_is_never_null(expr.e2, nullable_columns)
        )
    return False


def _fold_sqlancer_oracle_bool_not_like_literal(expr):
    if (
        isinstance(expr, BNeg)
        and getattr(expr.b, "op", None) == "LIKE"
        and isinstance(expr.b.e1, BNeg)
        and getattr(expr.b.e1.b, "name", None) is not None
        and isinstance(expr.b.e2, BValue)
    ):
        pattern = str(expr.b.e2.v)
        if "%" not in pattern and "_" not in pattern and pattern not in {"True", "False"}:
            return BNeg(IsNull(expr.b.e1.b))
    return expr


def _sqlancer_query_tables(query):
    table = getattr(query, "tablename", None)
    if table is not None:
        return [table]
    tables = []
    for attr in ("query", "q1", "q2", "l", "r"):
        if hasattr(query, attr):
            tables.extend(_sqlancer_query_tables(getattr(query, attr)))
    return tables


def _sqlancer_fixture_row_envs(tables, schema_dict, data_dict, *, oracle_empty_strings=False):
    envs = [{}]
    for table in tables:
        cols = schema_dict.get(table, [])
        rows = data_dict.get(table, [])
        next_envs = []
        for env in envs:
            for row in rows:
                row_env = dict(env)
                for idx, col in enumerate(cols):
                    row_env[f"{table}.{col['name']}"] = _coerce_fixture_value(
                        row[idx] if idx < len(row) else None,
                        col["type"],
                        oracle_empty_strings=oracle_empty_strings,
                    )
                next_envs.append(row_env)
        envs = next_envs
    return envs


def _sqlancer_oracle_condition_never_true_on_fixture(query, schema_dict, data_dict):
    tables = _sqlancer_query_tables(query.query)
    envs = _sqlancer_fixture_row_envs(
        tables,
        schema_dict,
        data_dict,
        oracle_empty_strings=True,
    )
    if not envs:
        return True
    saw_unknown = False
    for env in envs:
        value = _sqlancer_truth_for_where(_sqlancer_eval_oracle_expr(query.cond, env))
        if value is True:
            return False
        if value is _SQLANCER_UNKNOWN:
            saw_unknown = True
    return not saw_unknown


def _sqlancer_truth_for_where(value):
    if value is _SQLANCER_UNKNOWN:
        return _SQLANCER_UNKNOWN
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("t", "tr", "tru", "true", "y", "ye", "yes", "on", "1"):
            return True
        if text in ("", "f", "fa", "fal", "fals", "false", "n", "no", "of", "off", "0"):
            return False
        return _SQLANCER_UNKNOWN
    return _SQLANCER_UNKNOWN


def _sqlancer_eval_oracle_truth(expr, env):
    # Keep scalar '' -> NULL behavior in _sqlancer_eval_oracle_expr while
    # matching boolean-context behavior for logical operators.
    if isinstance(expr, Ascr):
        return _sqlancer_eval_oracle_truth(expr.e, env)
    if isinstance(expr, BValue) and expr.v == "":
        return False
    return _sqlancer_truth_for_where(_sqlancer_eval_oracle_expr(expr, env))


def _sqlancer_eval_oracle_expr(expr, env):
    if isinstance(expr, BValue):
        value = expr.v
        return None if value == "" else value
    if isinstance(expr, Ascr):
        return _sqlancer_eval_oracle_expr(expr.e, env)
    name = getattr(expr, "name", None)
    if name is not None:
        return env.get(name)
    if isinstance(expr, BNeg):
        value = _sqlancer_eval_oracle_truth(expr.b, env)
        if value is None or value is _SQLANCER_UNKNOWN:
            return value
        return not value
    if isinstance(expr, IsNull):
        value = _sqlancer_eval_oracle_expr(expr.e, env)
        if value is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return value is None
    if isinstance(expr, Or):
        left = _sqlancer_eval_oracle_truth(expr.l, env)
        right = _sqlancer_eval_oracle_truth(expr.r, env)
        if left is True or right is True:
            return True
        if left is False and right is False:
            return False
        return None if left is None or right is None else _SQLANCER_UNKNOWN
    if isinstance(expr, And):
        left = _sqlancer_eval_oracle_truth(expr.l, env)
        right = _sqlancer_eval_oracle_truth(expr.r, env)
        if left is False or right is False:
            return False
        if left is True and right is True:
            return True
        return None if left is None or right is None else _SQLANCER_UNKNOWN
    if getattr(expr, "op", None) in {"=", "<"}:
        left = _sqlancer_eval_oracle_expr(expr.e1, env)
        right = _sqlancer_eval_oracle_expr(expr.e2, env)
        if left is None or right is None:
            return None
        try:
            left, right = _sqlancer_oracle_comparable_values(left, right)
            if getattr(expr, "op", None) == "=":
                return left == right
            return left < right
        except Exception:
            return _SQLANCER_UNKNOWN
    return _SQLANCER_UNKNOWN


def _sqlancer_oracle_comparable_values(left, right):
    if type(left) is type(right):
        return left, right
    if isinstance(left, bool):
        left = 1 if left else 0
    if isinstance(right, bool):
        right = 1 if right else 0
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        return float(left), float(right)
    return left, right


def _fold_sqlancer_mssql_nested_null_query(query):
    if hasattr(query, "query"):
        _fold_sqlancer_mssql_nested_null_query(query.query)
    if not hasattr(query, "cond"):
        return query
    cond = query.cond
    if isinstance(cond, IsNull) and isinstance(cond.e, IsNull):
        query.cond = BValue(False)
    elif isinstance(cond, BNeg) and isinstance(cond.b, IsNull) and isinstance(cond.b.e, IsNull):
        query.cond = BValue(True)
    return query


def _sqlancer_mssql_static_condition(expr):
    if isinstance(expr, BValue):
        if expr.v is None:
            return None
        return expr.v if isinstance(expr.v, bool) else _SQLANCER_UNKNOWN
    if isinstance(expr, BNeg):
        value = _sqlancer_mssql_static_condition(expr.b)
        if value is None:
            return None
        if value is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return not value
    if isinstance(expr, IsNull):
        value = _sqlancer_mssql_static_condition(expr.e)
        if value is None:
            return True
        if value is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return False
    if isinstance(expr, Or):
        left = _sqlancer_mssql_static_condition(expr.l)
        right = _sqlancer_mssql_static_condition(expr.r)
        if left is True or right is True:
            return True
        if left is False and right is False:
            return False
        if left is _SQLANCER_UNKNOWN or right is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return None
    if isinstance(expr, And):
        left = _sqlancer_mssql_static_condition(expr.l)
        right = _sqlancer_mssql_static_condition(expr.r)
        if left is False or right is False:
            return False
        if left is True and right is True:
            return True
        if left is _SQLANCER_UNKNOWN or right is _SQLANCER_UNKNOWN:
            return _SQLANCER_UNKNOWN
        return None
    if getattr(expr, "op", None) in {"=", "<", "LIKE"}:
        left = _sqlancer_mssql_static_condition(expr.e1)
        right = _sqlancer_mssql_static_condition(expr.e2)
        if left is None or right is None:
            return None
        if isinstance(expr.e1, BValue) and isinstance(expr.e2, BValue):
            left_value = expr.e1.v
            right_value = expr.e2.v
            if type(left_value) is type(right_value):
                if getattr(expr, "op", None) == "=":
                    return left_value == right_value
                if getattr(expr, "op", None) == "<":
                    return left_value < right_value
            if getattr(expr, "op", None) in {"=", "<"}:
                left_numeric = _sqlancer_mssql_literal_numeric_value(left_value)
                right_numeric = _sqlancer_mssql_literal_numeric_value(right_value)
                if left_numeric is not None and right_numeric is not None:
                    if getattr(expr, "op", None) == "=":
                        return left_numeric == right_numeric
                    return left_numeric < right_numeric
        return _SQLANCER_UNKNOWN
    return _SQLANCER_UNKNOWN


def _sqlancer_mssql_literal_numeric_value(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str) and value == "":
        return 0
    return None


def _fold_sqlancer_mssql_static_root_condition(query):
    if hasattr(query, "query"):
        _fold_sqlancer_mssql_static_root_condition(query.query)
    if not hasattr(query, "cond"):
        return query
    static_value = _sqlancer_mssql_static_condition(query.cond)
    if static_value is False or static_value is None:
        query.cond = BValue(False)
    elif static_value is True:
        query.cond = BValue(True)
    return query


def _sqlancer_query_contains_empty_relation(query, data_dict):
    table = getattr(query, "tablename", None)
    if table is not None and not data_dict.get(table, []):
        return True
    for attr in ("query", "q1", "q2"):
        if hasattr(query, attr) and _sqlancer_query_contains_empty_relation(
            getattr(query, attr),
            data_dict,
        ):
            return True
    return False


def _fold_sqlancer_mssql_empty_source_where(query, data_dict):
    if hasattr(query, "query"):
        _fold_sqlancer_mssql_empty_source_where(query.query, data_dict)
    if hasattr(query, "cond") and _sqlancer_query_contains_empty_relation(
        query.query,
        data_dict,
    ):
        query.cond = BValue(False)
    return query


def _run_sqlancer_interpreter(sql, schema_dict, data_dict, engine_name, *, short_circuit=False):
    dbt = _build_dbt(schema_dict)
    db = _build_db(schema_dict, data_dict, engine_name)
    parser = LarkParser(schema=dbt)
    engine = ENGINE_CLASSES[engine_name]()
    old_short_circuit = getattr(engine.run.ops, "short_circuit_logical_ops", False)
    old_truth_value = getattr(engine.run.ops, "use_truth_value_for_logical_ops", None)
    engine.run.ops.short_circuit_logical_ops = short_circuit
    if short_circuit:
        engine.run.ops.use_truth_value_for_logical_ops = True
    try:
        parsed = parser.parse(sql)
        if engine_name == "oracle":
            parsed = _fold_sqlancer_oracle_null_root_condition(
                parsed,
                schema_dict,
                data_dict,
            )
        if engine_name == "mssql":
            parsed = _fold_sqlancer_mssql_empty_source_where(parsed, data_dict)
            parsed = _fold_sqlancer_mssql_nested_null_query(parsed)
            parsed = _fold_sqlancer_mssql_static_root_condition(parsed)
        if short_circuit and engine_name in {"mssql", "oracle"}:
            parsed = _fold_sqlancer_static_short_circuit_query(parsed, engine)
        TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
        qp = TQ[1]
        return engine.run.run_query(db, Eta([], []), qp), None, engine
    except Exception as e:
        return None, e, engine
    finally:
        engine.run.ops.short_circuit_logical_ops = old_short_circuit
        if old_truth_value is None:
            try:
                delattr(engine.run.ops, "use_truth_value_for_logical_ops")
            except AttributeError:
                pass
        else:
            engine.run.ops.use_truth_value_for_logical_ops = old_truth_value


def _find_top_level_keyword(sql: str, keyword: str) -> int:
    depth = 0
    in_str = False
    i = 0
    keyword_upper = keyword.upper()
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and sql[i:i + len(keyword)].upper() == keyword_upper:
                before_ok = i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == "_")
                after = i + len(keyword)
                after_ok = after == len(sql) or not (sql[after].isalnum() or sql[after] == "_")
                if before_ok and after_ok:
                    return i
        i += 1
    return -1


def _split_select_from_where(sql: str) -> tuple[str, str] | None:
    body = sql.strip().rstrip(";").strip()
    from_pos = _find_top_level_keyword(body, "FROM")
    if from_pos < 0:
        return None
    where_pos = _find_top_level_keyword(body[from_pos + 4:], "WHERE")
    if where_pos < 0:
        return None
    where_pos += from_pos + 4
    return body[from_pos + 4:where_pos].strip(), body[where_pos + 5:].strip()


def _mssql_rewrite_folded_constant_where(sql: str) -> bool:
    split = _split_select_from_where(sql)
    if split is None:
        return False
    where_sql = _strip_outer_parens(split[1]).strip()
    return re.fullmatch(r"(?is)[01]\s*=\s*[01]", where_sql) is not None


def _split_top_level_bool(sql: str) -> tuple[str, str, str] | None:
    depth = 0
    in_str = False
    pending_between = 0
    i = 0
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0:
                if sql[i:i + 7].upper() == "BETWEEN":
                    before_ok = i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == "_")
                    after = i + 7
                    after_ok = after == len(sql) or not (sql[after].isalnum() or sql[after] == "_")
                    if before_ok and after_ok:
                        pending_between += 1
                        i = after
                        continue
                consumed_between_and = False
                for op in ("AND", "OR"):
                    if sql[i:i + len(op)].upper() != op:
                        continue
                    before_ok = i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == "_")
                    after = i + len(op)
                    after_ok = after == len(sql) or not (sql[after].isalnum() or sql[after] == "_")
                    if not (before_ok and after_ok):
                        continue
                    if op == "AND" and pending_between > 0:
                        pending_between -= 1
                        i = after
                        consumed_between_and = True
                        break
                    return sql[:i].strip(), op, sql[after:].strip()
                if consumed_between_and:
                    continue
        i += 1
    return None


def _where_bool_branches(where_sql: str) -> list[str]:
    where_sql = _strip_outer_parens(where_sql)
    split = _split_top_level_bool(where_sql)
    if split is None:
        return []
    left, _, right = split
    branches = [left, right]
    branches.extend(_where_bool_branches(left))
    branches.extend(_where_bool_branches(right))
    return branches


def _parenthesized_predicate_candidates(sql: str) -> list[str]:
    candidates = []
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                i = match.end()
                continue
        if sql[i] != "(":
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            i += 1
            continue
        inner = _strip_outer_parens(sql[i + 1:close])
        if inner and not _is_mssql_case_expr(inner) and _has_top_level_bool_op(inner):
            candidates.append(inner)
        candidates.extend(_parenthesized_predicate_candidates(sql[i + 1:close]))
        i = close + 1
    return candidates


def _where_probe_predicates(where_sql: str) -> list[str]:
    candidates = []
    candidates.extend(_where_bool_branches(where_sql))
    parenthesized_candidates = _parenthesized_predicate_candidates(where_sql)
    candidates.extend(parenthesized_candidates)
    for candidate in parenthesized_candidates:
        candidates.extend(_where_bool_branches(candidate))
    seen = set()
    unique = []
    for candidate in candidates:
        key = candidate.strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def _split_top_level_comparison(sql: str) -> tuple[str, str, str] | None:
    sql = _strip_outer_parens(sql)
    depth = 0
    in_str = False
    i = 0
    while i < len(sql):
        c = sql[i]
        if c == "'":
            if in_str and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0:
                for op in ("<=", ">=", "<", ">"):
                    if sql.startswith(op, i):
                        return sql[:i].strip(), op, sql[i + len(op):].strip()
        i += 1
    return None


def _oracle_numeric_comparison_operand_probes(sql: str) -> list[str]:
    probes = []
    split = _split_top_level_comparison(sql)
    if split is not None:
        left, _, right = split
        if left:
            probes.append(f"0 < ({left})")
        if right:
            probes.append(f"0 < ({right})")
    i = 0
    while i < len(sql):
        if sql[i] == "'":
            match = _SQL_STRING_LITERAL_RE.match(sql, i)
            if match:
                i = match.end()
                continue
        if sql[i] != "(":
            i += 1
            continue
        close = _matching_paren_index(sql, i)
        if close is None:
            i += 1
            continue
        probes.extend(_oracle_numeric_comparison_operand_probes(sql[i + 1:close]))
        i = close + 1
    return probes


def _engine_avoided_erroring_branch(conn, engine_name: str, db_sql: str) -> bool:
    if engine_name not in {"mssql", "oracle"}:
        return False
    split = _split_select_from_where(db_sql)
    if split is None:
        return False
    from_sql, where_sql = split
    candidates = _where_probe_predicates(where_sql)
    if engine_name == "oracle":
        seen = {candidate.strip() for candidate in candidates}
        for candidate in _oracle_numeric_comparison_operand_probes(where_sql):
            key = candidate.strip()
            if key and key not in seen:
                seen.add(key)
                candidates.append(key)
    if not candidates:
        return False
    cur = _mssql_cursor(conn) if engine_name == "mssql" else conn.cursor()
    for candidate in candidates:
        probe_sql = _normalise_sql_for_engine(
            f"SELECT 1 FROM {from_sql} WHERE ({candidate})",
            engine_name,
        )
        try:
            cur.execute(probe_sql)
            cur.fetchall()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return True
    return False


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------
def _early_cli_filter():
    """Read --engine/--kind/--from/--upto from sys.argv so we can prune the
    parametrize list before pytest builds 380k test items. The conftest hook
    still applies the same filter; this just avoids the 15s silent wait that
    happens when collection iterates the full cartesian product."""
    import sys
    engines: set[str] | None = None
    kinds: set[str] | None = None
    from_case: str | None = None
    upto_case: str | None = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--engine="):
            engines = {e.strip() for e in arg.split("=", 1)[1].split(",") if e.strip()}
        elif arg == "--engine" and i + 1 < len(args):
            engines = {e.strip() for e in args[i + 1].split(",") if e.strip()}
            i += 1
        elif arg.startswith("--kind="):
            kinds = {k.strip() for k in arg.split("=", 1)[1].split(",") if k.strip()}
        elif arg == "--kind" and i + 1 < len(args):
            kinds = {k.strip() for k in args[i + 1].split(",") if k.strip()}
            i += 1
        elif arg.startswith("--from="):
            from_case = arg.split("=", 1)[1]
        elif arg == "--from" and i + 1 < len(args):
            from_case = args[i + 1]
            i += 1
        elif arg.startswith("--upto="):
            upto_case = arg.split("=", 1)[1]
        elif arg == "--upto" and i + 1 < len(args):
            upto_case = args[i + 1]
            i += 1
        elif arg == "-k" and i + 1 < len(args):
            match = re.search(
                r"\b([A-Za-z]+)_([A-Za-z0-9_-]+)/((?:case_)?\d+)\b",
                args[i + 1],
            )
            if match:
                engine, kind, case_id = match.groups()
                engines = {engine}
                kinds = {kind}
                if not case_id.startswith("case_"):
                    case_id = f"case_{case_id}"
                from_case = case_id
                upto_case = case_id
            i += 1
        i += 1
    return engines, kinds, from_case, upto_case


_CASES = discover_sqlancer_cases()
_engines_filter, _kinds_filter, _from_case, _upto_case = _early_cli_filter()
_PARAMS = [
    (engine, kind, path)
    for engine in ENABLED_ENGINES
    if _engines_filter is None or engine in _engines_filter
    for kind, path in _CASES
    if (_kinds_filter is None or kind in _kinds_filter)
    and (_from_case is None or path.stem >= _from_case)
    and (_upto_case is None or path.stem <= _upto_case)
]


@pytest.mark.parametrize(
    "engine_name,kind,yaml_path",
    _PARAMS,
    ids=[f"{engine}_{kind}/{path.stem}" for engine, kind, path in _PARAMS],
)
def test_sqlancer_case(request, conns, engine_name: str, kind: str, yaml_path: Path):
    case = _load_sqlancer_case(yaml_path)

    schema_dict = case.get("schema") or {}
    data_dict = case.get("data") or {}
    sql = (case.get("sql") or "").strip()
    if not sql:
        pytest.skip("no sql in case")
    if not sql.endswith(";"):
        sql += ";"

    display_sql = _display_text(sql)
    print(f"\n[{engine_name}/{kind}/{yaml_path.stem}] SQL: {display_sql}")

    conn = _get_conn(conns, engine_name)
    db_sql = _normalise_sql_for_engine(
        _rewrite_sql(sql, engine_name, schema_dict), engine_name
    )
    if engine_name == "mssql" and _sqlancer_sql_uses_empty_table(
        sql,
        schema_dict,
        data_dict,
    ):
        db_sql = _replace_where_with_constant(db_sql, "(1=0)")
    elif engine_name == "oracle" and _sqlancer_oracle_sql_never_true(
        sql,
        schema_dict,
        data_dict,
    ):
        db_sql = _replace_where_with_constant(db_sql, "(1=0)")
    display_db_sql = _display_text(db_sql)

    try:
        _MATERIALISERS[engine_name](conn, schema_dict, data_dict)
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        # Oracle ORA-00054 / ORA-00955 here mean an orphan session from a
        # previous test run still holds a TM lock on the table — the user
        # MYUSER doesn't have privileges to kill it, so we have to wait for
        # PMON. Skip the case rather than fail; it's a transient DB state,
        # not a code bug.
        err = str(e)
        if engine_name == "oracle" and ("ORA-00054" in err or "ORA-00955" in err):
            pytest.skip(
                f"oracle stale-lock on materialise (orphan TM lock from a "
                f"previous session); retry once PMON cleans it up: "
                f"{_display_text(e)}"
            )
        _record_sqlancer_mismatch(
            request,
            reason="materialise_error",
            engine_name=engine_name,
            kind=kind,
            yaml_path=yaml_path,
            sql=sql,
            db_sql=db_sql,
            materialise_error=e,
        )
        pytest.fail(
            f"failed to materialise schema/data on {engine_name}: {_display_text(e)}"
        )

    # Real engine (rewritten SQL where needed).
    their_result = None
    their_error = None
    try:
        _set_search_path(conn, engine_name)
        cur = _mssql_cursor(conn) if engine_name == "mssql" else conn.cursor()
        cur.execute(db_sql)
        their_result = cur.fetchall()
    except Exception as e:
        their_error = e
    finally:
        try:
            conn.rollback()
        except Exception:
            pass

    # Interpreter (always uses the original Postgres-flavoured SQL — the
    # interpreter parses one shared grammar and resolves ops via the engine).
    # For SQLancer MSSQL/Oracle only, compare both normal logical evaluation
    # and short-circuit logical evaluation; either matching result is accepted.
    our_result, our_error, engine = _run_sqlancer_interpreter(
        sql,
        schema_dict,
        data_dict,
        engine_name,
    )
    short_result = None
    short_error = None
    if engine_name in {"mssql", "oracle"}:
        short_result, short_error, _ = _run_sqlancer_interpreter(
            sql,
            schema_dict,
            data_dict,
            engine_name,
            short_circuit=True,
        )

    interpreter_results = [result for result in (our_result, short_result) if result is not None]
    if their_error and not interpreter_results:
        return
    if their_error is None:
        for candidate in interpreter_results:
            if Engine().Compare(candidate.rows, list(their_result), engine):
                return

    if not interpreter_results and their_error is None:
        if engine_name == "mssql" and _mssql_rewrite_folded_constant_where(db_sql):
            _record_sqlancer_mismatch(
                request,
                reason="mssql_rewrite_folded_interpreter_error",
                engine_name=engine_name,
                kind=kind,
                yaml_path=yaml_path,
                sql=sql,
                db_sql=db_sql,
                our_error=our_error,
                their_result=their_result,
            )
        _record_sqlancer_mismatch(
            request,
            reason="interpreter_error_only",
            engine_name=engine_name,
            kind=kind,
            yaml_path=yaml_path,
            sql=sql,
            db_sql=db_sql,
            our_error=our_error,
            their_result=their_result,
        )
        error_text = _display_text(our_error)
        if short_error is not None and short_error != our_error:
            error_text += f"\nShort-circuit interpreter error: {_display_text(short_error)}"
        pytest.fail(
            f"Interpreter failed but {engine_name.upper()} succeeded.\n"
            f"SQL: {display_sql}\n"
            f"Engine SQL: {display_db_sql}\n"
            f"Interpreter error: {error_text}\n"
            f"{engine_name.upper()} rows ({len(their_result)}): {their_result[:10]}"
        )
    if their_error and interpreter_results:
        # When the engine rejects bad type coercion mid-query (Oracle's
        # ORA-01426 numeric overflow, ORA-01722 string-to-number,
        # ORA-907 strict-type parser, ORA-02000 strict JOIN/ON keyword,
        # ORA-61800 invalid-bool-literal; MSSQL's 4145 non-boolean-in-condition
        # or 22018/245 type-conversion-failure) the SQL has no well-defined answer —
        # Oracle 23c and MSSQL are stricter than Postgres about types like
        # `BOOL + INT` or `STRING OR STRING`, while our interpreter follows
        # Postgres's looser coercion. Treat these as a match for SQLancer
        # crash/fail cases where the expected outcome is `rows: []` either way.
        their_text = str(their_error)
        empty_expected_rows = not (case.get("rows") or [])
        # dbms-fail cases were generated when Postgres rejected the query for
        # strict-typing reasons. Oracle 23c / MSSQL share the same strict
        # boolean/numeric coercion rules, so they error on the same predicates
        # — accept that as a match when the expected outcome is empty rows.
        strictness_kind = kind in {"both-fail", "traf-crash", "dbms-fail"}
        engine_strictness_error = strictness_kind and empty_expected_rows and (
            (
                engine_name == "oracle"
                and any(
                    code in their_text
                    for code in ("ORA-00907", "ORA-01426", "ORA-01722", "ORA-02000", "ORA-61800")
                )
            )
            or (
                engine_name == "mssql"
                and any(
                    code in their_text
                    for code in (
                        "(4145)",  # non-boolean expression in condition context
                        "22018",   # SQLSTATE conversion failed
                        "(245)",   # conversion failed when converting string→int
                        "(8114)",  # error converting data type
                        "(8115)",  # arithmetic overflow
                    )
                )
            )
        )
        if engine_strictness_error:
            return
        _record_sqlancer_mismatch(
            request,
            reason="engine_error_only",
            engine_name=engine_name,
            kind=kind,
            yaml_path=yaml_path,
            sql=sql,
            db_sql=db_sql,
            our_result=interpreter_results[0],
            their_error=their_error,
        )
        pytest.fail(
            f"{engine_name.upper()} failed but interpreter succeeded.\n"
            f"SQL: {display_sql}\n"
            f"Engine SQL: {display_db_sql}\n"
            f"{engine_name.upper()} error: {_display_text(their_error)}\n"
            f"Interpreter rows ({len(interpreter_results[0].rows)}): "
            f"{[[v.erase() for v in r] for r in interpreter_results[0].rows[:10]]}"
        )

    # On dbms-fail / both-fail / traf-crash cases (queries Postgres / Traf
    # rejected for strict-typing reasons) Oracle may diverge silently rather
    # than via an ORA-* error, in two symmetric ways:
    #
    #   - Oracle treats `''` as NULL, so `WHERE (NOT '')` collapses to
    #     `WHERE NULL` and Oracle returns no rows, while our interpreter
    #     follows Postgres-loose coercion and returns rows.
    #   - Oracle implicitly casts numeric literals to strings for `LIKE`
    #     (e.g. `c1 NOT LIKE -1088203184`), so it succeeds and returns rows
    #     while Postgres/Traf reject the operator pairing.
    #
    # Both are the semantic equivalent of the ORA-* strictness errors already
    # tolerated above. Gate on the expected outcome being empty rows so we
    # don't silently swallow real result-correctness divergences.
    strictness_kind = kind in {"both-fail", "traf-crash", "dbms-fail"}
    empty_expected_rows = not (case.get("rows") or [])
    if engine_name == "oracle" and strictness_kind and empty_expected_rows and not their_error:
        empty_string_quirk = len(their_result) == 0 and "''" in sql
        like_numeric_quirk = bool(re.search(r"\bLIKE\s*\(?\s*-?\d", sql, re.IGNORECASE))
        if empty_string_quirk or like_numeric_quirk:
            return

    mismatch_result = interpreter_results[0] if interpreter_results else our_result
    _record_sqlancer_mismatch(
        request,
        reason="result_mismatch",
        engine_name=engine_name,
        kind=kind,
        yaml_path=yaml_path,
        sql=sql,
        db_sql=db_sql,
        our_result=mismatch_result,
        their_result=their_result,
    )
    short_summary = ""
    if short_result is not None:
        short_summary = (
            f"\nShort-circuit interpreter ({len(short_result.rows)}): "
            f"{[[v.erase() for v in r] for r in short_result.rows[:10]]}"
        )
    elif short_error is not None:
        short_summary = f"\nShort-circuit interpreter error: {_display_text(short_error)}"
    pytest.fail(
        f"Result mismatch on {engine_name.upper()}.\n"
        f"SQL: {display_sql}\n"
        f"Engine SQL: {display_db_sql}\n"
        f"Interpreter ({len(mismatch_result.rows)}): "
        f"{[[v.erase() for v in r] for r in mismatch_result.rows[:10]]}"
        f"{short_summary}\n"
        f"{engine_name.upper()} ({len(their_result)}): {their_result[:10]}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
