"""
Exhaustive Postgres test — loads a pre-generated query corpus from JSONL and
runs every query through the interpreter and Postgres, asserting agreement.

Pipeline mirrors test/calcite/test_calcite_pairs.py:
    parse (skip if Lark fails) → typecheck → run interpreter → run Postgres
    → Engine().Compare.

Corpus path is selected by `EXHAUSTIVE_QUERIES_FILE`. Default is
`test/exhaustive/corpus/floor.jsonl`. Regenerate with:
    python -m test.exhaustive.enumerate dump <preset> <path>
"""

import json
import os
from pathlib import Path

import pytest

from interpreter.Runtime import Eta
from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.type.RelationType import RelationType


DEFAULT_CORPUS = Path(__file__).parent / "corpus" / "floor.jsonl"


def _load_corpus() -> list[dict]:
    path = Path(os.environ.get("EXHAUSTIVE_QUERIES_FILE", DEFAULT_CORPUS))
    if not path.exists():
        raise RuntimeError(
            f"corpus not found at {path}. Generate with: "
            f"python -m test.exhaustive.enumerate dump <preset> {path}"
        )
    with open(path) as f:
        return [json.loads(line) for line in f]


_CORPUS = _load_corpus()


@pytest.mark.parametrize(
    "sql",
    [entry["sql"] for entry in _CORPUS],
    ids=[f"q{i:04d}" for i in range(len(_CORPUS))],
)
def test_exhaustive(exhaustive_fixture, sql):
    conn, db, dbt = exhaustive_fixture

    parser = LarkParser(schema=dbt)
    engine = Postgres()

    sql_query = sql if sql.rstrip().endswith(";") else sql + ";"

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
        cur = conn.cursor()
        cur.execute(sql_query)
        their_result = cur.fetchall()
    except Exception as e:
        their_error = e
    finally:
        conn.rollback()

    if our_error and their_error:
        return
    if our_error and not their_error:
        pytest.fail(
            f"Interpreter failed but Postgres succeeded.\n"
            f"SQL: {sql_query}\n"
            f"Interpreter error: {our_error}\n"
            f"Postgres result: {their_result}"
        )
    if their_error and not our_error:
        pytest.fail(
            f"Postgres failed but interpreter succeeded.\n"
            f"SQL: {sql_query}\n"
            f"Postgres error: {their_error}\n"
            f"Interpreter result: {our_result.rows}"
        )

    if not Engine().Compare(our_result.rows, their_result, engine):
        pytest.fail(
            f"Result mismatch.\n"
            f"SQL: {sql_query}\n"
            f"Interpreter: {our_result.rows}\n"
            f"Postgres:    {their_result}"
        )
