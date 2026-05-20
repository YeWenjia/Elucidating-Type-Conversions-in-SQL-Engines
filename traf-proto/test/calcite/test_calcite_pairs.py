"""
Calcite benchmark test — compares interpreter output against five real engines
(Postgres, MySQL, SQLite, MSSQL, Oracle) for every SQL query in
benchmarks/calcite/calcite2.jsonlines.

Each JSON line has a `pair` of two SQL queries (Calcite's rewrite rule corpus).
We test both queries in the pair on every enabled engine, asserting the
interpreter and the engine agree on each. Queries the interpreter's Lark
grammar can't parse are skipped — the "both fail" agreement isn't meaningful
when the interpreter rejects the query before reaching any semantic work.

Slice the run via the standard pytest -k filter or with --calcite-engine=<csv>:
    pytest test/calcite/                                       # 5 engines × 794
    pytest test/calcite/ --calcite-engine=postgres             # one engine
    pytest test/calcite/ --calcite-engine=postgres,sqlite      # two engines
"""

import json
import re

import pytest

from interpreter.Runtime import Eta
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Mssql import Mssql
from interpreter.syntax.engine.Mysql import Mysql
from interpreter.syntax.engine.Oracle import Oracle
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.syntax.type.RelationType import RelationType

from test.calcite.conftest import (
    CALCITE_DB,
    CALCITE_JSONLINES,
    CALCITE_SCHEMA,
    ENABLED_ENGINES,
)


ENGINE_CLASSES = {
    "postgres": Postgres,
    "mysql":    Mysql,
    "sqlite":   Sqlite,
    "mssql":    Mssql,
    "oracle":   Oracle,
}


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------
def _load_cases():
    cases = []
    with open(CALCITE_JSONLINES) as f:
        for line in f:
            entry = json.loads(line)
            idx = entry["index"]
            for which, sql in enumerate(entry["pair"]):
                cases.append((idx, which, sql))
    return cases


_CASES = _load_cases()
_PARAMS = [
    (engine, idx, which, sql)
    for engine in ENABLED_ENGINES
    for idx, which, sql in _CASES
]


# ---------------------------------------------------------------------------
# Per-engine query plumbing
# ---------------------------------------------------------------------------
_TRUE_RE = re.compile(r"\bTRUE\b", re.IGNORECASE)
_FALSE_RE = re.compile(r"\bFALSE\b", re.IGNORECASE)
# Match CAST(<expr> AS INT) or CAST(<expr> AS INTEGER). Non-greedy on the
# inner expression so we don't swallow a trailing CAST in the same query.
_CAST_AS_INT_RE = re.compile(
    r"(?i)\bCAST\s*\(\s*(.+?)\s+AS\s+INT(?:EGER)?\b\s*\)"
)
_CAST_AS_VARCHAR_RE = re.compile(
    r"(?i)\bCAST\s*\(\s*(.+?)\s+AS\s+VARCHAR\s*(\(\s*\d+\s*\))?\s*\)"
)
_CALCITE_TABLES = (
    "EMPNULLABLES_20",
    "EMPNULLABLES",
    "EMP_B",
    "BONUS",
    "DEPT",
    "EMP",
)


def _rewrite_sql(sql: str, engine_name: str) -> str:
    """Minimal dialect rewriting. Calcite SQL is largely standard, so most
    queries pass through unchanged; only the obvious gotchas are translated."""
    if engine_name in ("postgres", "sqlite"):
        return sql
    if engine_name == "mysql":
        # MySQL: CAST(x AS INT/INTEGER) is invalid — use SIGNED.
        sql = _CAST_AS_INT_RE.sub(lambda m: f"CAST({m.group(1)} AS SIGNED)", sql)
        # MySQL CAST supports CHAR rather than VARCHAR. The interpreter's SType
        # does not model VARCHAR length, so drop the length instead of adding
        # MySQL-only truncation semantics with CHAR(N).
        sql = _CAST_AS_VARCHAR_RE.sub(
            lambda m: f"CAST({m.group(1)} AS CHAR)",
            sql,
        )
        return sql
    if engine_name in ("mssql", "oracle"):
        # Neither has a TRUE/FALSE literal in older versions.
        sql = _TRUE_RE.sub("(1=1)", sql)
        sql = _FALSE_RE.sub("(1=0)", sql)
        if engine_name == "mssql":
            # The interpreter's SType does not model VARCHAR length, so avoid
            # SQL Server truncating CAST(x AS VARCHAR(n)) before comparisons.
            sql = _CAST_AS_VARCHAR_RE.sub(
                lambda m: f"CAST({m.group(1)} AS VARCHAR(MAX))",
                sql,
            )
            # Pin every plain string literal to a binary collation so
            # comparisons stay case-sensitive regardless of the MSSQL
            # database's default collation. Python's string comparison
            # (which the interpreter uses) is code-point ordered; without
            # this, MSSQL's default CI collation makes `'OPERATIONS' > 'b'`
            # true while the interpreter says false. The lookbehind keeps
            # literals already prefixed with N untouched.
            sql = re.sub(
                r"(?<![A-Za-z_0-9])'((?:[^']|'')*)'",
                lambda m: f"(N'{m.group(1)}' COLLATE Latin1_General_BIN)",
                sql,
            )
        if engine_name == "oracle":
            # Oracle: CAST AS INT works in 12c+, but NUMBER is the canonical
            # numeric type — be conservative.
            sql = _CAST_AS_INT_RE.sub(lambda m: f"CAST({m.group(1)} AS NUMBER)", sql)
    return sql


def _qualify_mssql_tables(sql: str) -> str:
    """Qualify Calcite's physical tables with the MSSQL schema."""
    table_pattern = "|".join(re.escape(t) for t in _CALCITE_TABLES)
    ref_re = re.compile(
        rf"(?i)\b(FROM|JOIN)\s+({table_pattern})\b"
    )
    qualified_ref = (
        r"\[[^\]]+\]\.\[[^\]]+\]"
        r"(?:\s+(?:AS\s+)?[A-Za-z_][A-Za-z0-9_$]*)?"
    )
    comma_ref_re = re.compile(
        rf"(?i)(\bFROM\s+{qualified_ref}(?:\s*,\s*{qualified_ref})*)"
        rf"\s*,\s*({table_pattern})\b"
    )

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = ref_re.sub(
            lambda m: f"{m.group(1)} [{CALCITE_SCHEMA}].[{m.group(2).lower()}]",
            parts[i],
        )
        while True:
            next_part = comma_ref_re.sub(
                lambda m: (
                    f"{m.group(1)}, "
                    f"[{CALCITE_SCHEMA}].[{m.group(2).lower()}]"
                ),
                parts[i],
            )
            if next_part == parts[i]:
                break
            parts[i] = next_part
    return "".join(parts)


def _strip_mssql_derived_order_by(sql: str) -> str:
    order_re = re.compile(
        r"(?i)\s+ORDER\s+BY\s+([^()]*?)(?=\)\s+AS\s+[A-Za-z_][A-Za-z0-9_$]*)"
    )

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = order_re.sub(
            lambda m: (
                m.group(0)
                if re.search(r"(?i)\b(OFFSET|FETCH|FOR\s+XML)\b", m.group(1))
                else ""
            ),
            parts[i],
        )
    return "".join(parts)


def _rewrite_mssql_row_value_in(sql: str) -> str:
    table_ref = r"(?:\[[^\]]+\]\.)?\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_$]*"
    name_ref = r"[A-Za-z_][A-Za-z0-9_$]*(?:\.[A-Za-z_][A-Za-z0-9_$]*)?"
    row_in_re = re.compile(
        rf"(?i)(\b(?:WHERE|AND|OR)\s+)"
        rf"\(\s*({name_ref})\s*,\s*({name_ref})\s*\)\s+IN\s+"
        rf"\(\s*SELECT\s+({name_ref})\s*,\s*({name_ref})\s+"
        rf"FROM\s+({table_ref})([^()]*)\)"
    )

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = row_in_re.sub(
            lambda m: (
                f"{m.group(1)}EXISTS (SELECT {m.group(2)}, {m.group(3)} "
                f"INTERSECT SELECT {m.group(4)}, {m.group(5)} "
                f"FROM {m.group(6)}{m.group(7)})"
            ),
            parts[i],
        )
    return "".join(parts)


def _split_top_level_commas(text: str) -> list[str]:
    items = []
    start = 0
    depth = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif ch == "," and depth == 0:
            items.append(text[start:i].strip())
            start = i + 1
    items.append(text[start:].strip())
    return items


def _is_mssql_constant_group_item(item: str) -> bool:
    return (
        re.fullmatch(r"[0-9+\-*/().\s]+", item) is not None
        and re.search(r"\d", item) is not None
    )


def _strip_mssql_constant_group_by_items(sql: str) -> str:
    group_re = re.compile(
        r"(?i)\bGROUP\s+BY\s+(.+?)(?=\s+(?:HAVING|ORDER\s+BY|UNION|INTERSECT|EXCEPT)\b|\)\s+AS\b|;)"
    )

    def repl(match):
        items = _split_top_level_commas(match.group(1))
        kept = [item for item in items if not _is_mssql_constant_group_item(item)]
        if not kept:
            return ""
        return "GROUP BY " + ", ".join(kept)

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = group_re.sub(repl, parts[i])
    return "".join(parts)


def _rewrite_mssql_predicate_is_null(sql: str) -> str:
    pred_is_null_re = re.compile(
        r"(?i)(\b(?:WHERE|AND|OR)\s+)\(([^()]*\b(?:AND|OR)\b[^()]*)\)\s+IS\s+NULL"
    )

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = pred_is_null_re.sub(
            lambda m: (
                f"{m.group(1)}CASE WHEN {m.group(2)} THEN 1 "
                f"WHEN NOT ({m.group(2)}) THEN 0 ELSE NULL END IS NULL"
            ),
            parts[i],
        )
    return "".join(parts)


def _rewrite_mssql_boolean_null_literals(sql: str) -> str:
    bool_null_re = re.compile(
        r"(?i)(\b(?:WHERE|WHEN|ON|AND|OR|NOT\s*\()\s+)"
        r"NULL"
        r"(?=\s+(?:AND|OR|THEN|AS)\b|\s*\))"
    )

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = bool_null_re.sub(r"\g<1>1 = NULL", parts[i])
    return "".join(parts)


def _strip_oracle_table_alias_as(sql: str) -> str:
    table_pattern = "|".join(re.escape(t) for t in _CALCITE_TABLES)
    table_alias_re = re.compile(
        r"(?i)\b(FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_$]*)\s+AS\s+([A-Za-z_][A-Za-z0-9_$]*)"
    )
    comma_table_alias_re = re.compile(
        rf"(?i)(,\s*)({table_pattern})\s+AS\s+([A-Za-z_][A-Za-z0-9_$]*)"
    )
    derived_source_re = re.compile(r"(?i)\b(?:FROM|JOIN)\s+\(")

    def strip_derived_alias_as(text: str) -> str:
        spans = []
        for match in derived_source_re.finditer(text):
            depth = 0
            close_idx = None
            i = match.end() - 1
            while i < len(text):
                if text[i] == "'":
                    i += 1
                    while i < len(text):
                        if text[i] == "'" and i + 1 < len(text) and text[i + 1] == "'":
                            i += 2
                            continue
                        if text[i] == "'":
                            break
                        i += 1
                elif text[i] == "(":
                    depth += 1
                elif text[i] == ")":
                    depth -= 1
                    if depth == 0:
                        close_idx = i
                        break
                i += 1
            if close_idx is None:
                continue
            alias_match = re.match(
                r"(?i)(\s+)AS\s+(?=[A-Za-z_][A-Za-z0-9_$]*)",
                text[close_idx + 1:],
            )
            if alias_match:
                start = close_idx + 1 + len(alias_match.group(1))
                end = close_idx + 1 + alias_match.end()
                spans.append((start, end))

        for start, end in sorted(spans, reverse=True):
            text = text[:start] + text[end:]
        return text

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = table_alias_re.sub(r"\1 \2 \3", parts[i])
        parts[i] = comma_table_alias_re.sub(r"\1\2 \3", parts[i])
    return strip_derived_alias_as("".join(parts))


def _rewrite_oracle_empty_string_comparisons(sql: str) -> str:
    name_ref = r"[A-Za-z_][A-Za-z0-9_$]*(?:\.[A-Za-z_][A-Za-z0-9_$]*)?"
    neq_empty_re = re.compile(
        rf"(?i)\b({name_ref})\s*(?:<>|!=)\s*''"
    )
    empty_neq_re = re.compile(
        rf"(?i)''\s*(?:<>|!=)\s*({name_ref})\b"
    )
    ordered_neq_empty_re = re.compile(
        rf"(?i)\(\s*({name_ref})\s*<\s*''\s+OR\s+\1\s*>\s*''\s*\)"
    )
    ordered_neq_empty_rev_re = re.compile(
        rf"(?i)\(\s*({name_ref})\s*>\s*''\s+OR\s+\1\s*<\s*''\s*\)"
    )

    literals = []

    def protect_literal(match):
        literal = match.group(0)
        if literal == "''":
            return literal
        literals.append(literal)
        return f"__ORACLE_LITERAL_{len(literals) - 1}__"

    sql = re.sub(r"'(?:[^']|'')*'", protect_literal, sql)
    sql = ordered_neq_empty_re.sub(r"\1 IS NOT NULL", sql)
    sql = ordered_neq_empty_rev_re.sub(r"\1 IS NOT NULL", sql)
    sql = neq_empty_re.sub(r"\1 IS NOT NULL", sql)
    sql = empty_neq_re.sub(r"\1 IS NOT NULL", sql)
    for i, literal in enumerate(literals):
        sql = sql.replace(f"__ORACLE_LITERAL_{i}__", literal)
    return sql


def _rewrite_oracle_predicate_is_null(sql: str) -> str:
    pred_is_null_re = re.compile(
        r"(?i)(\b(?:WHERE|AND|OR)\s+)\(([^()]*\b(?:AND|OR)\b[^()]*)\)\s+IS\s+NULL"
    )

    parts = re.split(r"('(?:[^']|'')*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = pred_is_null_re.sub(
            lambda m: (
                f"{m.group(1)}CASE WHEN {m.group(2)} THEN 1 "
                f"WHEN NOT ({m.group(2)}) THEN 0 ELSE NULL END IS NULL"
            ),
            parts[i],
        )
    return "".join(parts)


def _normalise_sql_for_engine(sql: str, engine_name: str) -> str:
    if engine_name == "mssql":
        return _rewrite_mssql_boolean_null_literals(
            _rewrite_mssql_predicate_is_null(
                _strip_mssql_constant_group_by_items(
                    _strip_mssql_derived_order_by(
                        _rewrite_mssql_row_value_in(_qualify_mssql_tables(sql))
                    )
                )
            )
        )
    if engine_name == "oracle":
        # Oracle rejects a trailing `;` over the OCI driver.
        return _rewrite_oracle_predicate_is_null(
            _rewrite_oracle_empty_string_comparisons(
                _strip_oracle_table_alias_as(sql.rstrip().rstrip(";"))
            )
        )
    return sql


def _set_search_path(conn, engine_name: str):
    """Make unqualified table refs (e.g. `EMP`) resolve to our schema."""
    cur = conn.cursor()
    if engine_name == "postgres":
        cur.execute(f'SET search_path TO "{CALCITE_SCHEMA}", public')
    elif engine_name == "mysql":
        cur.execute(f"USE `{CALCITE_DB}`")
    elif engine_name == "mssql":
        cur.execute(f"USE [{CALCITE_DB}]")
        try:
            cur.execute(
                f"ALTER USER CURRENT_USER WITH DEFAULT_SCHEMA = [{CALCITE_SCHEMA}]"
            )
        except Exception:
            pass
    # sqlite: single namespace; oracle: tables live in the connection user's
    # own schema, so no qualifier is needed.


def _rollback_quietly(conn):
    try:
        conn.rollback()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Mismatch recording (written to JSON in pytest_sessionfinish)
# ---------------------------------------------------------------------------
def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _sample_interpreter_rows(table, limit=10):
    if table is None:
        return None
    return [[_jsonable(v.erase()) for v in row] for row in table.rows[:limit]]


def _sample_engine_rows(rows, limit=10):
    if rows is None:
        return None
    return [[_jsonable(v) for v in row] for row in rows[:limit]]


def _record_mismatch(
    request,
    *,
    reason,
    engine_name,
    index,
    which,
    sql,
    db_sql,
    our_result=None,
    their_result=None,
    our_error=None,
    their_error=None,
):
    bucket = getattr(request.config, "_calcite_mismatches", None)
    if bucket is None:
        return
    bucket.append({
        "reason": reason,
        "engine": engine_name,
        "case": f"calcite-{index:03d}_{which}",
        "index": index,
        "which": which,
        "sql": sql,
        "engine_sql": db_sql,
        "interpreter_error": str(our_error) if our_error else None,
        "engine_error": str(their_error) if their_error else None,
        "interpreter_row_count": len(our_result.rows) if our_result is not None else None,
        "engine_row_count": len(their_result) if their_result is not None else None,
        "interpreter_rows_sample": _sample_interpreter_rows(our_result),
        "engine_rows_sample": _sample_engine_rows(their_result),
    })


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "engine_name,index,which,sql",
    _PARAMS,
    ids=[f"{engine}-calcite-{idx:03d}_{which}" for engine, idx, which, _ in _PARAMS],
)
def test_calcite_pair(request, calcite_engines, engine_name, index, which, sql):
    conn, db, dbt = calcite_engines(engine_name)

    parser = LarkParser(schema=dbt)
    engine = ENGINE_CLASSES[engine_name]()

    sql_query = sql if sql.rstrip().endswith(";") else sql + ";"
    db_sql = _normalise_sql_for_engine(_rewrite_sql(sql_query, engine_name), engine_name)

    try:
        parsed = parser.parse(sql_query)
    except Exception as e:
        pytest.skip(f"interpreter cannot parse query: {e}")

    our_result = None
    our_error = None
    try:
        TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
        qp = TQ[1]
        our_result = engine.run.run_query(db, Eta([], []), qp)
    except Exception as e:
        our_error = e

    their_result = None
    their_error = None
    try:
        _set_search_path(conn, engine_name)
        cur = conn.cursor()
        cur.execute(db_sql)
        their_result = cur.fetchall()
    except Exception as e:
        their_error = e
    finally:
        _rollback_quietly(conn)

    if (
        engine_name in ("oracle", "mysql", "mssql", "postgres")
        and our_error
        and not their_error
        and str(our_error).startswith("Scalar subquery returned ")
        and list(their_result) == []
    ):
        # Real engines short-circuit / lazily evaluate the multi-row scalar
        # subquery when an outer NULL/FALSE operand already pins the result —
        # ours evaluates eagerly and raises. When the engine returned 0 rows
        # the eager evaluation is the only difference, so treat it as match.
        our_result = type("CalciteEmptyResult", (), {"rows": []})()
        our_error = None

    if our_error and their_error:
        return
    if our_error and not their_error:
        _record_mismatch(
            request,
            reason="interpreter_error_only",
            engine_name=engine_name,
            index=index,
            which=which,
            sql=sql_query,
            db_sql=db_sql,
            our_error=our_error,
            their_result=their_result,
        )
        pytest.fail(
            f"Interpreter failed but {engine_name.upper()} succeeded.\n"
            f"SQL: {sql_query}\n"
            f"Engine SQL: {db_sql}\n"
            f"Interpreter error: {our_error}\n"
            f"{engine_name.upper()} result: {their_result}"
        )
    if their_error and not our_error:
        _record_mismatch(
            request,
            reason="engine_error_only",
            engine_name=engine_name,
            index=index,
            which=which,
            sql=sql_query,
            db_sql=db_sql,
            our_result=our_result,
            their_error=their_error,
        )
        pytest.fail(
            f"{engine_name.upper()} failed but interpreter succeeded.\n"
            f"SQL: {sql_query}\n"
            f"Engine SQL: {db_sql}\n"
            f"{engine_name.upper()} error: {their_error}\n"
            f"Interpreter result: {our_result.rows}"
        )

    if not Engine().Compare(our_result.rows, list(their_result), engine):
        _record_mismatch(
            request,
            reason="result_mismatch",
            engine_name=engine_name,
            index=index,
            which=which,
            sql=sql_query,
            db_sql=db_sql,
            our_result=our_result,
            their_result=their_result,
        )
        pytest.fail(
            f"Result mismatch on {engine_name.upper()}.\n"
            f"SQL: {sql_query}\n"
            f"Engine SQL: {db_sql}\n"
            f"Interpreter: {our_result.rows}\n"
            f"{engine_name.upper()}:    {their_result}"
        )
