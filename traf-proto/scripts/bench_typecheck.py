"""
Benchmark: the interpreter's type-checking time.

The thing being measured is **the interpreter's typechecker**, not any
external DBMS. No DBMS connection is made — the script needs only the
interpreter modules, SQLite (for reading the cached Spider schemas), and
PyYAML.

Measures two workloads:
  1. All Spider YAML queries (~3469 queries across ~137 folders).
  2. N randomly generated queries (default N=100000).

Only the call to ``typechecker.typecheck_query(...)`` is timed — parsing,
YAML loading, schema setup, and query generation are excluded. Both
successful and error-raising type-checks are included in the samples (a
rejected query also exercises real type-checking work).

Reports N / min / max / mean / std (in milliseconds and microseconds).

Run from the repository root (``impl/traf-prototype``):

    python -m scripts.bench_typecheck                 # both benchmarks
    python -m scripts.bench_typecheck --spider        # spider only
    python -m scripts.bench_typecheck --generated --n 100000
    python -m scripts.bench_typecheck --repeat 3      # run each benchmark 3 times

Use ``--save-csv-dir`` to dump per-query timings (one row per query) for
later analysis (e.g. in a notebook).
"""

from __future__ import annotations

import argparse
import csv
import gc
import os
import re
import sqlite3
import statistics
import sys
import time
from pathlib import Path

import yaml

# Make sure ``interpreter`` is importable when running this script directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from interpreter.lark_parser import LarkParser
from interpreter.queryGenerator import dbt as gen_dbt, generate
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.type.RelationType import NameType, RelationType
from interpreter.syntax.type.ValueType import DTType, RType, SType, ZType


SPIDER_BASE = REPO_ROOT / "benchmarks" / "spider"
SQLITE_CACHE = REPO_ROOT / ".sqlite_cache"


def make_typechecker():
    """Return the interpreter's typechecker.

    The Typechecker class lives in ``interpreter/Typechecker.py`` and is
    parameterized by per-dialect ``Ops``. We pick Postgres for instantiation
    because it is the dialect used elsewhere in the paper; the timing measures
    the interpreter, not the DBMS.
    """
    return Postgres().typechecker


# Generator-syntax dialect used when emitting random queries. This only
# affects the *syntax* the generator picks (e.g. ``CAST(x AS DECIMAL(10,1))``
# vs ``CAST(x AS FLOAT)``). The typechecker being timed is the interpreter's.
GENERATOR_SYNTAX = "Postgres"


# ---------------------------------------------------------------------------
# Spider schema loading (SQLite-backed; no external server required)
# ---------------------------------------------------------------------------

def _pragma_type_to_vtype(data_type: str):
    dtype = (data_type or "").lower().strip()
    if dtype in {"int", "integer", "bigint", "smallint", "tinyint", "mediumint", "int4", "int8"}:
        return ZType()
    if dtype in {"real", "float", "double", "double precision", "numeric", "decimal", "money"}:
        return RType()
    if dtype in {"date", "time", "datetime", "timestamp"} or dtype.startswith("timestamp"):
        return DTType()
    return SType()


def _ensure_sqlite_schema(folder: Path) -> Path | None:
    """Make sure a SQLite db exists with the folder's schema loaded.

    Returns the db path, or ``None`` if no ``db.sql`` is available.
    """
    SQLITE_CACHE.mkdir(exist_ok=True)
    db_path = SQLITE_CACHE / f"{folder.name}.db"

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        if cur.fetchone()[0] > 0:
            return db_path

        db_sql_path = folder / "tables" / "db.sql"
        if not db_sql_path.exists():
            return None

        sql_script = db_sql_path.read_text()
        sql_script = re.sub(r"^\s*BEGIN\s*;", "", sql_script, flags=re.IGNORECASE | re.MULTILINE)
        sql_script = re.sub(r"^\s*COMMIT\s*;", "", sql_script, flags=re.IGNORECASE | re.MULTILINE)
        cur.executescript(sql_script)
        conn.commit()
        return db_path
    finally:
        conn.close()


def get_dbt_for_folder(folder: Path) -> dict | None:
    """Build the ``dbt`` (schema dict) for a Spider folder using SQLite."""
    db_path = _ensure_sqlite_schema(folder)
    if db_path is None:
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        table_names = [row[0] for row in cur.fetchall()]

        dbt: dict[str, RelationType] = {}
        for table_name in table_names:
            cur.execute(f'PRAGMA table_info("{table_name}")')
            name_types = []
            for row in cur.fetchall():
                col_name = row[1]
                col_type = row[2]
                name_types.append(NameType(col_name, _pragma_type_to_vtype(col_type)))
            dbt[table_name.lower()] = RelationType(name_types)
        return dbt
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Statistics + reporting
# ---------------------------------------------------------------------------

def _fmt_stats(samples_seconds):
    n = len(samples_seconds)
    if n == 0:
        return {
            "n": 0,
            "min_ms": 0.0, "max_ms": 0.0, "mean_ms": 0.0, "std_ms": 0.0,
            "min_us": 0.0, "max_us": 0.0, "mean_us": 0.0, "std_us": 0.0,
            "total_s": 0.0,
        }
    ms = [s * 1_000.0 for s in samples_seconds]
    us = [s * 1_000_000.0 for s in samples_seconds]
    std_ms = statistics.stdev(ms) if n > 1 else 0.0
    std_us = statistics.stdev(us) if n > 1 else 0.0
    return {
        "n": n,
        "min_ms": min(ms), "max_ms": max(ms),
        "mean_ms": statistics.mean(ms), "std_ms": std_ms,
        "min_us": min(us), "max_us": max(us),
        "mean_us": statistics.mean(us), "std_us": std_us,
        "total_s": sum(samples_seconds),
    }


def _print_stats(name: str, stats: dict):
    print(f"\n=== {name} ===")
    print(f"  N         = {stats['n']}")
    print(f"  total     = {stats['total_s']:.3f} s")
    print(f"  min       = {stats['min_ms']:.4f} ms  ({stats['min_us']:.2f} us)")
    print(f"  max       = {stats['max_ms']:.4f} ms  ({stats['max_us']:.2f} us)")
    print(f"  mean      = {stats['mean_ms']:.4f} ms  ({stats['mean_us']:.2f} us)")
    print(f"  std       = {stats['std_ms']:.4f} ms  ({stats['std_us']:.2f} us)")


def _save_csv(path: Path, header: list, rows: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  [saved] {path}")


# ---------------------------------------------------------------------------
# Spider benchmark
# ---------------------------------------------------------------------------

def bench_spider(verbose: bool = False, save_csv: Path | None = None):
    print("\n" + "=" * 72)
    print("Benchmark 1/2 : Interpreter type-checking on Spider queries")
    print("=" * 72)

    if not SPIDER_BASE.exists():
        print(f"[ERROR] Spider benchmark dir not found at {SPIDER_BASE}")
        return None

    typechecker = make_typechecker()
    timings: list[float] = []
    csv_rows: list[list] = []
    parse_errors = 0
    typecheck_errors = 0
    schema_errors = 0
    skipped = 0

    folders = sorted(
        f for f in SPIDER_BASE.iterdir()
        if f.is_dir() and "[IGNORE]" not in f.name
    )
    print(f"  folders: {len(folders)}")

    for folder in folders:
        try:
            dbt = get_dbt_for_folder(folder)
        except Exception as e:
            schema_errors += 1
            if verbose:
                print(f"  [SCHEMA-ERROR] {folder.name}: {e}")
            continue
        if not dbt:
            schema_errors += 1
            if verbose:
                print(f"  [SCHEMA-ERROR] {folder.name}: empty dbt")
            continue

        try:
            parser = LarkParser(schema=dbt)
        except Exception as e:
            schema_errors += 1
            if verbose:
                print(f"  [PARSER-INIT-ERROR] {folder.name}: {e}")
            continue

        yaml_files = sorted(
            y for y in folder.glob("*.yaml") if "[IGNORE]" not in y.name
        )
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r") as f:
                    yaml_data = yaml.safe_load(f)
            except Exception:
                skipped += 1
                continue

            sql_query = (yaml_data or {}).get("sql") or ""
            sql_query = sql_query.strip()
            if not sql_query:
                skipped += 1
                continue
            if not sql_query.endswith(";"):
                sql_query += ";"

            try:
                parsed = parser.parse(sql_query)
            except Exception as e:
                parse_errors += 1
                if verbose:
                    print(f"  [PARSE-ERROR] {yaml_file.relative_to(SPIDER_BASE)}: {e}")
                continue

            gc.disable()
            t0 = time.perf_counter()
            tc_error: Exception | None = None
            try:
                typechecker.typecheck_query(dbt, RelationType([]), parsed)
            except Exception as e:
                tc_error = e
            t1 = time.perf_counter()
            gc.enable()

            elapsed = t1 - t0
            timings.append(elapsed)
            if tc_error is not None:
                typecheck_errors += 1
                if verbose:
                    print(f"  [TC-ERROR] {yaml_file.relative_to(SPIDER_BASE)}: {tc_error}")
            if save_csv is not None:
                csv_rows.append([
                    folder.name,
                    yaml_file.name,
                    elapsed,
                    "error" if tc_error is not None else "ok",
                ])

        if verbose:
            print(f"  [{folder.name}] cumulative typechecked: {len(timings)}")

    print(
        f"\n  spider summary: success={len(timings) - typecheck_errors}, "
        f"typecheck_errors={typecheck_errors}, "
        f"parse_errors={parse_errors}, "
        f"schema_errors={schema_errors}, skipped={skipped}"
    )

    stats = _fmt_stats(timings)
    _print_stats("Interpreter type-checking — Spider", stats)

    if save_csv is not None:
        _save_csv(save_csv, ["folder", "yaml", "seconds", "status"], csv_rows)

    return stats


# ---------------------------------------------------------------------------
# Generated-queries benchmark
# ---------------------------------------------------------------------------

def bench_generated(
    n: int = 100_000,
    verbose: bool = False,
    save_csv: Path | None = None,
    seed: int | None = None,
):
    print("\n" + "=" * 72)
    print(f"Benchmark 2/2 : Interpreter type-checking on {n} randomly generated queries")
    print("=" * 72)

    if seed is not None:
        import random
        random.seed(seed)

    typechecker = make_typechecker()
    parser = LarkParser(schema=gen_dbt)
    dbt = gen_dbt

    timings: list[float] = []
    csv_rows: list[list] = []
    gen_errors = 0
    parse_errors = 0
    typecheck_errors = 0

    i = 0
    attempts = 0
    # Give ourselves headroom in case some generated queries fail to parse.
    max_attempts = n * 5

    progress_step = max(n // 20, 1)

    while i < n and attempts < max_attempts:
        attempts += 1
        try:
            sql_query = generate(GENERATOR_SYNTAX)
        except Exception as e:
            gen_errors += 1
            if verbose and gen_errors <= 5:
                print(f"  [GEN-ERROR] {e}")
            continue

        try:
            parsed = parser.parse(sql_query)
        except Exception as e:
            parse_errors += 1
            if verbose and parse_errors <= 5:
                print(f"  [PARSE-ERROR] {e}")
            continue

        gc.disable()
        t0 = time.perf_counter()
        tc_error: Exception | None = None
        try:
            typechecker.typecheck_query(dbt, RelationType([]), parsed)
        except Exception as e:
            tc_error = e
        t1 = time.perf_counter()
        gc.enable()

        elapsed = t1 - t0
        timings.append(elapsed)
        if tc_error is not None:
            typecheck_errors += 1
            if verbose and typecheck_errors <= 5:
                print(f"  [TC-ERROR] {tc_error}")
        if save_csv is not None:
            csv_rows.append([
                i,
                elapsed,
                len(sql_query),
                "error" if tc_error is not None else "ok",
            ])
        i += 1

        if verbose and i % progress_step == 0:
            print(f"  progress: {i:>7} / {n}  (attempts={attempts})")

    print(
        f"\n  generated summary: typechecked={len(timings)} "
        f"(success={len(timings) - typecheck_errors}, "
        f"typecheck_errors={typecheck_errors}), "
        f"attempts={attempts}, gen_errors={gen_errors}, parse_errors={parse_errors}"
    )

    stats = _fmt_stats(timings)
    _print_stats("Interpreter type-checking — generated", stats)

    if save_csv is not None:
        _save_csv(save_csv, ["index", "seconds", "query_length", "status"], csv_rows)

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _print_machine_info():
    import platform
    print("\n" + "=" * 72)
    print("Machine info")
    print("=" * 72)
    print(f"  platform         : {platform.platform()}")
    print(f"  processor        : {platform.processor()}")
    print(f"  python           : {platform.python_version()} ({platform.python_implementation()})")
    try:
        cpu_count = os.cpu_count()
        print(f"  cpu_count        : {cpu_count}")
    except Exception:
        pass
    try:
        import subprocess
        if sys.platform == "darwin":
            out = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], stderr=subprocess.DEVNULL
            )
            print(f"  cpu_brand        : {out.decode().strip()}")
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spider", action="store_true", help="Run only the Spider benchmark.")
    ap.add_argument("--generated", action="store_true", help="Run only the generated-queries benchmark.")
    ap.add_argument("--n", type=int, default=100_000, help="Number of generated queries (default 100000).")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for generated queries (default 42).")
    ap.add_argument("--repeat", type=int, default=1, help="Run each benchmark this many times (default 1).")
    ap.add_argument("--save-csv-dir", type=Path, default=None,
                    help="Optional directory to write per-query CSVs to.")
    ap.add_argument("--verbose", action="store_true", help="Print progress and per-folder/error logs.")
    args = ap.parse_args()

    run_spider = args.spider or not (args.spider or args.generated)
    run_gen = args.generated or not (args.spider or args.generated)

    _print_machine_info()

    spider_runs: list[dict] = []
    gen_runs: list[dict] = []

    for rep in range(args.repeat):
        if args.repeat > 1:
            print(f"\n############ REPEAT {rep + 1} / {args.repeat} ############")

        if run_spider:
            csv_path = None
            if args.save_csv_dir is not None:
                csv_path = args.save_csv_dir / f"spider_typecheck_run{rep+1}.csv"
            stats = bench_spider(verbose=args.verbose, save_csv=csv_path)
            if stats is not None:
                spider_runs.append(stats)

        if run_gen:
            csv_path = None
            if args.save_csv_dir is not None:
                csv_path = args.save_csv_dir / f"generated_typecheck_run{rep+1}.csv"
            stats = bench_generated(
                n=args.n,
                verbose=args.verbose,
                save_csv=csv_path,
                seed=(args.seed + rep) if args.seed is not None else None,
            )
            gen_runs.append(stats)

    if args.repeat > 1:
        print("\n" + "=" * 72)
        print("Cross-run summary (per-run statistics)")
        print("=" * 72)

        def _summary(label, runs):
            if not runs:
                return
            print(f"\n{label}")
            print(f"  {'run':>4}  {'N':>8}  {'min(ms)':>10}  {'max(ms)':>10}  {'mean(ms)':>10}  {'std(ms)':>10}")
            for k, r in enumerate(runs, 1):
                print(
                    f"  {k:>4}  {r['n']:>8}  "
                    f"{r['min_ms']:>10.4f}  {r['max_ms']:>10.4f}  "
                    f"{r['mean_ms']:>10.4f}  {r['std_ms']:>10.4f}"
                )

        _summary("Spider:", spider_runs)
        _summary("Generated:", gen_runs)


if __name__ == "__main__":
    main()
