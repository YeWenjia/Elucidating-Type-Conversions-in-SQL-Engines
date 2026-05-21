#!/usr/bin/env python3
"""Run the paper's claimed SQL examples against configured DBMSs.

The manifest below is intentionally explicit: each case records the query used
in the paper and the per-engine outcome claimed by the text or table. The runner
creates the small relation R(A,B) from Table 1 and checks observed behavior
against those claims.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


ENGINES = ("postgres", "mssql", "oracle", "mysql", "sqlite")


@dataclass(frozen=True)
class Outcome:
    status: str
    rows: tuple[tuple[Any, ...], ...] = ()
    paper_label: str | None = None


@dataclass(frozen=True)
class Case:
    case_id: str
    section: str
    query: str
    expected: dict[str, Outcome]
    note: str = ""


def ok(rows: Iterable[Iterable[Any]], paper_label: str | None = None) -> Outcome:
    return Outcome("ok", tuple(tuple(row) for row in rows), paper_label)


def err(paper_label: str = "error") -> Outcome:
    return Outcome("error", paper_label=paper_label)


def repeated(value: Any, count: int = 3) -> tuple[tuple[Any, ...], ...]:
    return tuple((value,) for _ in range(count))


def repeated_pair(v1: Any, v2: Any, count: int = 3) -> tuple[tuple[Any, ...], ...]:
    return tuple((v1, v2) for _ in range(count))


TABLE_1_CASES = [
    Case(
        "T1-E1",
        "Table 1",
        "SELECT 1.1 + 1 FROM R",
        {engine: ok(repeated(Decimal("2.1"))) for engine in ENGINES},
    ),
    Case(
        "T1-E2",
        "Table 1",
        "SELECT '1' + 1 FROM R",
        {engine: ok(repeated(2)) for engine in ENGINES},
    ),
    Case(
        "T1-E3",
        "Table 1",
        "SELECT '1.1' + 1 FROM R",
        {
            "postgres": err("static error"),
            "mssql": err("runtime error"),
            "oracle": ok(repeated(Decimal("2.1"))),
            "mysql": ok(repeated(Decimal("2.1"))),
            "sqlite": ok(repeated(Decimal("2.1"))),
        },
    ),
    Case(
        "T1-E4",
        "Table 1",
        "SELECT '1.1' + 1.1 FROM R",
        {engine: ok(repeated(Decimal("2.2"))) for engine in ENGINES},
    ),
    Case(
        "T1-E5",
        "Table 1",
        "SELECT '1' + '1' FROM R",
        {
            "postgres": err("static error"),
            "mssql": ok(repeated("11")),
            "oracle": ok(repeated(2)),
            "mysql": ok(repeated(2)),
            "sqlite": ok(repeated(2)),
        },
    ),
    Case(
        "T1-E6",
        "Table 1",
        "SELECT 'a' + '2b' FROM R",
        {
            "postgres": err("static error"),
            "mssql": ok(repeated("a2b")),
            "oracle": err("runtime error"),
            "mysql": ok(repeated(2)),
            "sqlite": ok(repeated(2)),
        },
    ),
    Case(
        "T1-E7",
        "Table 1",
        "SELECT 1 + A FROM R WHERE B = 20",
        {
            "postgres": err("static error"),
            "mssql": ok(((2,),)),
            "oracle": ok(((2,),)),
            "mysql": ok(((2,),)),
            "sqlite": ok(((2,),)),
        },
    ),
    Case(
        "T1-E8",
        "Table 1",
        "SELECT 1 + A FROM R WHERE B = 10",
        {
            "postgres": err("static error"),
            "mssql": err("runtime error"),
            "oracle": err("runtime error"),
            "mysql": ok(((1,),)),
            "sqlite": ok(((1,),)),
        },
    ),
    Case(
        "T1-E9",
        "Table 1",
        "SELECT 1 + A FROM (SELECT '2' AS A FROM R) B",
        {
            "postgres": err("static error"),
            "mssql": ok(repeated(3)),
            "oracle": ok(repeated(3)),
            "mysql": ok(repeated(3)),
            "sqlite": ok(repeated(3)),
        },
        note="The inner SELECT includes FROM R so the query is syntactically valid on Oracle 21c.",
    ),
    Case(
        "T1-E10",
        "Table 1",
        "SELECT 1 FROM R WHERE '1' < 2",
        {
            "postgres": ok(repeated(1)),
            "mssql": ok(repeated(1)),
            "oracle": ok(repeated(1)),
            "mysql": ok(repeated(1)),
            "sqlite": ok(()),
        },
    ),
    Case(
        "T1-E11",
        "Table 1",
        "SELECT 1 FROM R WHERE '1.1' < 2",
        {
            "postgres": err("static error"),
            "mssql": err("runtime error"),
            "oracle": ok(repeated(1)),
            "mysql": ok(repeated(1)),
            "sqlite": ok(()),
        },
    ),
    Case(
        "T1-E12",
        "Table 1",
        "SELECT '1.1' FROM R INTERSECT SELECT 1.1 FROM R",
        {
            "postgres": ok(((Decimal("1.1"),),)),
            "mssql": ok(((Decimal("1.1"),),)),
            "oracle": err("static error"),
            "mysql": ok((("1.1",),)),
            "sqlite": ok(()),
        },
    ),
    Case(
        "T1-E13",
        "Table 1",
        "SELECT '1.1' FROM R INTERSECT SELECT 1 FROM R",
        {
            "postgres": err("static error"),
            "mssql": err("runtime error"),
            "oracle": err("static error"),
            "mysql": ok(()),
            "sqlite": ok(()),
        },
    ),
]


SECTION_4_CASES = [
    Case(
        "S4-PG-1",
        "Section 4 / PostgreSQL",
        "(SELECT 1 FROM R) INTERSECT (SELECT 1.0 FROM R)",
        {"postgres": ok(((1,),), "singleton numeric value; clients may render it as 1 or 1.0")},
    ),
    Case(
        "S4-PG-2",
        "Section 4 / PostgreSQL",
        "(SELECT '-1.0' FROM R) INTERSECT (SELECT -1.0 FROM R)",
        {"postgres": ok(((Decimal("-1.0"),),))},
    ),
    Case(
        "S4-PG-3",
        "Section 4 / PostgreSQL",
        "SELECT CAST('1.1' AS DECIMAL(10,1)) FROM R",
        {"postgres": ok(repeated(Decimal("1.1")))},
    ),
    Case(
        "S4-PG-4",
        "Section 4 / PostgreSQL",
        "SELECT CAST('1.1' AS INT) FROM R",
        {"postgres": err("static error")},
    ),
    Case(
        "S4-PG-5",
        "Section 4 / PostgreSQL",
        "SELECT 1 + 1.1 FROM R",
        {"postgres": ok(repeated(Decimal("2.1")))},
    ),
    Case(
        "S4-PG-6",
        "Section 4 / PostgreSQL",
        "SELECT '1' + 1.1 FROM R",
        {"postgres": ok(repeated(Decimal("2.1")))},
    ),
    Case(
        "S4-PG-7",
        "Section 4 / PostgreSQL",
        "SELECT '1' + '1' FROM R",
        {"postgres": err("static error")},
    ),
    Case(
        "S4-SQLite-1",
        "Section 4 / SQLite",
        "SELECT '0' < 1 FROM R",
        {"sqlite": ok(repeated(0))},
    ),
    Case(
        "S4-SQLite-2",
        "Section 4 / SQLite",
        "SELECT '0' < CAST(1 AS INT) FROM R",
        {"sqlite": ok(repeated(1))},
    ),
    Case(
        "S4-SQLite-3",
        "Section 4 / SQLite",
        "SELECT '0hi' < CAST(1 AS INT) FROM R",
        {"sqlite": ok(repeated(0))},
    ),
    Case(
        "S4-SQLite-4",
        "Section 4 / SQLite",
        "SELECT CAST('12.3hi' AS INT), CAST('hi' AS INT) FROM R",
        {"sqlite": ok(repeated_pair(12, 0))},
    ),
    Case(
        "S4-TR-1",
        "Section 4 / translation",
        "SELECT CAST('1.1' AS DECIMAL(10,1)) + 1 FROM R",
        {"postgres": ok(repeated(Decimal("2.1")))},
    ),
    Case(
        "S4-TR-2",
        "Section 4 / translation",
        "SELECT 1 FROM R WHERE CAST('1' AS INT) < 2",
        {"sqlite": ok(repeated(1))},
    ),
    Case(
        "S4-TR-3",
        "Section 4 / translation",
        "SELECT 1 FROM R WHERE '1' < CAST(2 AS INT)",
        {"sqlite": ok(repeated(1))},
    ),
]


CASES = tuple(TABLE_1_CASES + SECTION_4_CASES)


SCHEMA_SQL = {
    "sqlite": [
        "DROP TABLE IF EXISTS R",
        "CREATE TABLE R(A VARCHAR(255), B INT)",
    ],
    "postgres": [
        "DROP TABLE IF EXISTS R",
        "CREATE TABLE R(A VARCHAR(255), B INT)",
    ],
    "mysql": [
        "DROP TABLE IF EXISTS R",
        "CREATE TABLE R(A VARCHAR(255), B INT)",
    ],
    "mssql": [
        "IF OBJECT_ID('R', 'U') IS NOT NULL DROP TABLE R",
        "CREATE TABLE R(A VARCHAR(255), B INT)",
    ],
    "oracle": [
        "DROP TABLE R PURGE",
        "CREATE TABLE R(A VARCHAR2(255), B NUMBER(10))",
    ],
}

INSERT_SQL = {
    "default": "INSERT INTO R(A, B) VALUES (?, ?)",
    "postgres": "INSERT INTO R(A, B) VALUES (%s, %s)",
    "mysql": "INSERT INTO R(A, B) VALUES (%s, %s)",
    "oracle": "INSERT INTO R(A, B) VALUES (:1, :2)",
}

R_ROWS = (("Bob", 10), ("1", 20), ("1.1", 30))


def load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for non-SQLite engine configs") from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def connect(engine: str, config: dict[str, Any] | None):
    if engine == "sqlite":
        return sqlite3.connect(":memory:")

    if config is None or engine not in config:
        raise RuntimeError(f"missing configuration for {engine}")

    if engine == "postgres":
        import psycopg2

        c = config[engine]
        kwargs = {
            "host": c.get("host"),
            "port": c.get("port"),
            "dbname": c.get("database"),
            "user": c.get("username"),
            "password": c.get("password"),
        }
        return psycopg2.connect(**{k: v for k, v in kwargs.items() if v is not None})

    if engine == "mysql":
        import mysql.connector

        c = config[engine]
        return mysql.connector.connect(
            host=c.get("host"),
            port=c.get("port", 3306),
            database=c.get("database"),
            user=c.get("username"),
            password=c.get("password"),
        )

    if engine == "mssql":
        import pyodbc

        c = config[engine]
        return pyodbc.connect(
            Driver=c.get("driver"),
            server=c.get("server"),
            database=c.get("database"),
            user=c.get("username"),
            password=c.get("password"),
        )

    if engine == "oracle":
        try:
            import oracledb
        except ImportError:
            import cx_Oracle as oracledb

        c = config[engine]
        return oracledb.connect(user=c.get("user"), password=c.get("password"), dsn=c.get("dsn"))

    raise RuntimeError(f"unsupported engine {engine}")


def execute_ddl(cursor: Any, engine: str, statement: str) -> None:
    try:
        cursor.execute(statement)
    except Exception:
        if engine == "oracle" and statement.startswith("DROP TABLE"):
            return
        raise


def setup_schema(conn: Any, engine: str) -> None:
    cursor = conn.cursor()
    try:
        for statement in SCHEMA_SQL[engine]:
            execute_ddl(cursor, engine, statement)
        insert = INSERT_SQL.get(engine, INSERT_SQL["default"])
        for row in R_ROWS:
            cursor.execute(insert, row)
        conn.commit()
    finally:
        cursor.close()


def run_query(conn: Any, engine: str, query: str) -> tuple[str, list[tuple[Any, ...]] | str]:
    cursor = conn.cursor()
    try:
        statement = query.rstrip(";")
        cursor.execute(statement)
        if cursor.description is None:
            rows: list[tuple[Any, ...]] = []
        else:
            rows = [tuple(row) for row in cursor.fetchall()]
        try:
            conn.rollback()
        except Exception:
            pass
        return "ok", rows
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        return "error", f"{type(exc).__name__}: {exc}"
    finally:
        cursor.close()


def decimal_or_none(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return Decimal(str(value))
    return None


def compare_value(expected: Any, observed: Any) -> bool:
    if isinstance(expected, str):
        return isinstance(observed, str) and observed == expected

    expected_num = decimal_or_none(expected)
    observed_num = decimal_or_none(observed)
    if expected_num is not None and observed_num is not None:
        return abs(expected_num - observed_num) <= Decimal("0.000001")

    return observed == expected


def row_key(row: tuple[Any, ...]) -> tuple[str, ...]:
    key = []
    for value in row:
        num = decimal_or_none(value)
        if num is not None:
            key.append(f"num:{num.normalize()}")
        else:
            key.append(f"{type(value).__name__}:{value!r}")
    return tuple(key)


def rows_match(expected: tuple[tuple[Any, ...], ...], observed: list[tuple[Any, ...]]) -> bool:
    if len(expected) != len(observed):
        return False

    unmatched = list(observed)
    for expected_row in expected:
        found = None
        for index, observed_row in enumerate(unmatched):
            if len(expected_row) == len(observed_row) and all(
                compare_value(e, o) for e, o in zip(expected_row, observed_row)
            ):
                found = index
                break
        if found is None:
            return False
        unmatched.pop(found)
    return not unmatched


def format_rows(rows: Iterable[Iterable[Any]]) -> str:
    return repr(sorted((tuple(row) for row in rows), key=row_key))


def selected_cases(engine: str, section_filter: str | None) -> list[Case]:
    cases = [case for case in CASES if engine in case.expected]
    if section_filter:
        cases = [case for case in cases if section_filter.lower() in case.section.lower()]
    return cases


def run_engine(engine: str, config: dict[str, Any] | None, section_filter: str | None) -> tuple[int, int]:
    conn = connect(engine, config)
    try:
        setup_schema(conn, engine)
        failures = 0
        total = 0
        for case in selected_cases(engine, section_filter):
            total += 1
            expected = case.expected[engine]
            status, payload = run_query(conn, engine, case.query)
            if status != expected.status:
                failures += 1
                print(f"FAIL {engine} {case.case_id}: expected {expected.paper_label}, got {status}")
                print(f"  query: {case.query}")
                print(f"  observed: {payload}")
            elif status == "ok" and not rows_match(expected.rows, payload):  # type: ignore[arg-type]
                failures += 1
                print(f"FAIL {engine} {case.case_id}: row mismatch")
                print(f"  query: {case.query}")
                print(f"  expected: {format_rows(expected.rows)}")
                print(f"  observed: {format_rows(payload)}")  # type: ignore[arg-type]
            else:
                print(f"PASS {engine} {case.case_id}")
        return total, failures
    finally:
        conn.close()


def list_cases() -> None:
    for case in CASES:
        engines = ", ".join(case.expected)
        print(f"{case.case_id}\t{case.section}\t[{engines}]\t{case.query}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        choices=("all", *ENGINES),
        default="sqlite",
        help="DBMS to audit. Defaults to sqlite because it needs no server.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("test/engines/config.yml"),
        help="YAML config for non-SQLite engines.",
    )
    parser.add_argument("--section", help="Only run cases whose section label contains this text.")
    parser.add_argument("--list", action="store_true", help="List manifest cases and exit.")
    parser.add_argument(
        "--skip-unavailable",
        action="store_true",
        help="When --engine all is used, skip engines whose connector/config is unavailable.",
    )
    args = parser.parse_args(argv)

    if args.list:
        list_cases()
        return 0

    engines = list(ENGINES) if args.engine == "all" else [args.engine]
    config = None
    if any(engine != "sqlite" for engine in engines):
        config = load_config(args.config)

    totals = Counter()
    for engine in engines:
        try:
            total, failures = run_engine(engine, config, args.section)
            totals["cases"] += total
            totals["failures"] += failures
        except Exception as exc:
            if args.engine == "all" and args.skip_unavailable:
                print(f"SKIP {engine}: {exc}")
                continue
            raise

    print(f"Summary: {totals['cases']} cases, {totals['failures']} failures")
    return 1 if totals["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
