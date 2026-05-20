"""
Exhaustive SQL enumerator — mirrors the grammar used by
interpreter/queryGenerator.py but enumerates instead of sampling, skips
aggregates, and is lazy with a hard cap.

Every level is a Python generator (`yield`) so the Cartesian product is never
materialized. `enumerate_queries()` wraps the stream in an `islice` whose upper
bound is set by the `max_queries` argument — the only way a caller can OOM is
to raise that cap and max-out the budgets at the same time.

Start with the defaults (all depths at 0) to see the floor. Raise budgets
gradually.
"""

from dataclasses import dataclass
from itertools import islice, product
from typing import Iterator


@dataclass(frozen=True)
class GenTable:
    alias: str
    cols: tuple[str, ...]


@dataclass(frozen=True)
class GenQuery:
    sql: str
    out_cols: tuple[str, ...]


@dataclass(frozen=True)
class Budgets:
    # Expression nesting: 0 = leaf only; 1 = one '+' or CAST; 2 = nested.
    max_expr_depth: int = 0
    # Comparison composition: 0 = single comp; 1 = one AND/OR; 2 = two levels.
    max_comp_depth: int = 0
    # Subqueries in FROM and in IN/EXISTS.
    max_sub_depth: int = 0
    # Set operations (UNION/EXCEPT/INTERSECT) — 0 disables them entirely.
    max_set_depth: int = 0
    # Number of tables in a single FROM (cross product).
    max_from_tables: int = 1
    # Number of columns a SELECT projects.
    max_cols: int = 1
    cast_types: tuple[str, ...] = ("DECIMAL(10,1)",)
    literals: tuple[str, ...] = ("1", "'a'", "NULL")
    # Hard cap on the total number of queries yielded. None = no cap (careful).
    max_queries: int | None = 2000


# Default base tables from the `interpreter` Postgres DB.
BASE_TABLES: tuple[GenTable, ...] = (
    GenTable("ta", ("age", "name", "height")),
    GenTable("tb", ("realage", "fullname", "fullheight")),
    GenTable("tc", ("newage", "newname", "newheight")),
)


def _names(tables: tuple[GenTable, ...]) -> Iterator[str]:
    for t in tables:
        for c in t.cols:
            yield f"{t.alias}.{c}"


def _expr(tables: tuple[GenTable, ...], depth: int, b: Budgets) -> Iterator[str]:
    yield from _names(tables)
    for lit in b.literals:
        yield lit
    if depth <= 0:
        return
    # Nested expressions use the NEXT-lower depth on both sides so we cap growth.
    # We materialize the previous level once (small at low budgets) — the dedupe
    # here also prevents the trivial "leaf + leaf" explosion.
    sub = list(_expr(tables, depth - 1, b))
    for a, c in product(sub, sub):
        yield f"({a} + {c})"
    for a in sub:
        for t in b.cast_types:
            yield f"CAST({a} AS {t})"


def _comp(tables: tuple[GenTable, ...], depth: int, b: Budgets,
          sub_depth: int) -> Iterator[str]:
    exprs = list(_expr(tables, b.max_expr_depth, b))
    for a, c in product(exprs, exprs):
        yield f"{a} < {c}"
        yield f"{a} = {c}"
    for e in exprs:
        yield f"({e} IS NULL)"
    if sub_depth < b.max_sub_depth:
        # Enumerate scalar-column subqueries on demand for IN.
        for e in exprs:
            for q in _query(depth=0, b=b, sub_depth=sub_depth + 1):
                if len(q.out_cols) == 1:
                    yield f"{e} IN ({q.sql})"
        for q in _query(depth=0, b=b, sub_depth=sub_depth + 1):
            yield f"EXISTS ({q.sql})"
    if depth <= 0:
        return
    inner = list(_comp(tables, depth - 1, b, sub_depth))
    for a, c in product(inner, inner):
        yield f"({a} AND {c})"
        yield f"({a} OR {c})"


def _from(b: Budgets, sub_depth: int) -> Iterator[tuple[str, tuple[GenTable, ...]]]:
    for t in BASE_TABLES:
        yield t.alias, (t,)
    if b.max_from_tables >= 2:
        for x, y in product(BASE_TABLES, BASE_TABLES):
            if x.alias == y.alias:
                continue
            yield f"{x.alias}, {y.alias}", (x, y)
    if sub_depth < b.max_sub_depth:
        for idx, q in enumerate(_query(depth=0, b=b, sub_depth=sub_depth + 1)):
            alias = f"s{sub_depth + 1}_{idx}"
            yield f"({q.sql}) {alias}", (GenTable(alias, q.out_cols),)


def _cols(tables: tuple[GenTable, ...], b: Budgets) -> Iterator[tuple[str, tuple[str, ...]]]:
    exprs = list(_expr(tables, b.max_expr_depth, b))
    for n in range(1, b.max_cols + 1):
        if n == 1:
            for e in exprs:
                yield f"{e} AS c0", ("c0",)
        else:
            for combo in product(exprs, repeat=n):
                parts = [f"{e} AS c{i}" for i, e in enumerate(combo)]
                aliases = tuple(f"c{i}" for i in range(n))
                yield ", ".join(parts), aliases


def _select(b: Budgets, sub_depth: int) -> Iterator[GenQuery]:
    for from_sql, tables in _from(b, sub_depth):
        for col_sql, col_aliases in _cols(tables, b):
            yield GenQuery(f"SELECT {col_sql} FROM {from_sql}", col_aliases)
            for cond in _comp(tables, b.max_comp_depth, b, sub_depth):
                yield GenQuery(
                    f"SELECT {col_sql} FROM {from_sql} WHERE {cond}",
                    col_aliases,
                )


def _query(depth: int, b: Budgets, sub_depth: int = 0) -> Iterator[GenQuery]:
    # Plain SELECTs first.
    if depth <= 0 or b.max_set_depth <= 0:
        yield from _select(b, sub_depth)
        return
    # Include the plain-SELECT universe at this level too.
    base = list(_select(b, sub_depth))
    yield from base
    deeper = list(_query(depth - 1, b, sub_depth))
    # Set ops require equal arity on both sides.
    by_arity: dict[int, list[GenQuery]] = {}
    for q in deeper:
        by_arity.setdefault(len(q.out_cols), []).append(q)
    for qs in by_arity.values():
        for a, c in product(qs, qs):
            for op in ("UNION", "EXCEPT", "INTERSECT"):
                yield GenQuery(f"{a.sql} {op} {c.sql}", a.out_cols)


def enumerate_queries(b: Budgets | None = None) -> list[GenQuery]:
    """Return a deduplicated list of queries up to Budgets.max_queries."""
    b = b or Budgets()
    stream = _query(depth=b.max_set_depth, b=b)
    if b.max_queries is not None:
        stream = islice(stream, b.max_queries)
    seen: set[str] = set()
    out: list[GenQuery] = []
    for q in stream:
        if q.sql in seen:
            continue
        seen.add(q.sql)
        out.append(q)
    return out


PRESETS: dict[str, Budgets] = {
    "floor":  Budgets(max_queries=200),
    "small":  Budgets(max_comp_depth=1, max_sub_depth=1, max_queries=2000),
    "medium": Budgets(max_expr_depth=1, max_sub_depth=1, max_comp_depth=0, max_queries=100000),
}


def _dump_jsonl(qs: list[GenQuery], path: str) -> None:
    import json
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        for q in qs:
            f.write(json.dumps({"sql": q.sql, "out_cols": list(q.out_cols)}) + "\n")


if __name__ == "__main__":
    # Two modes:
    #   <preset>                 — smoke print: count + first/last samples.
    #   dump <preset> <path>     — write JSONL to <path>, one query per line.
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "dump":
        if len(sys.argv) != 4:
            raise SystemExit("usage: python -m test.exhaustive.enumerate dump <preset> <path>")
        preset, path = sys.argv[2], sys.argv[3]
        if preset not in PRESETS:
            raise SystemExit(f"unknown preset: {preset}")
        qs = enumerate_queries(PRESETS[preset])
        _dump_jsonl(qs, path)
        print(f"wrote {len(qs)} queries to {path}")
        sys.exit(0)

    preset = sys.argv[1] if len(sys.argv) > 1 else "floor"
    if preset not in PRESETS:
        raise SystemExit(f"unknown preset: {preset}")
    b = PRESETS[preset]
    qs = enumerate_queries(b)
    print(f"preset={preset} budgets={b}")
    print(f"queries={len(qs)}")
    for q in qs[:5]:
        print("  ", q.sql)
    if len(qs) >= 5:
        print("  ...")
        for q in qs[-2:]:
            print("  ", q.sql)
