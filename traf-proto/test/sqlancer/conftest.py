"""
Pytest options for the SQLancer benchmark suite.

The benchmark has tens of thousands of cases (organised by kind subfolder)
and each runs against five engines, so the cartesian product is enormous.
These options let you slice the run by engine, by kind, and by case-id range
so the suite stays tractable during development.

Examples:
    pytest test/sqlancer/                                       # everything
    pytest test/sqlancer/ --engine=postgres                     # one engine
    pytest test/sqlancer/ --engine=postgres,sqlite              # two engines
    pytest test/sqlancer/ --kind=postgres-traf-mismatch         # one kind
    pytest test/sqlancer/ --engine=postgres --kind=postgres-benign --limit=200
    pytest test/sqlancer/ --from=case_000100 --upto=case_000999
"""

import json
from collections import Counter
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption(
        "--engine",
        dest="sqlancer_engines",
        default=None,
        help="Comma-separated list of engines to test "
             "(postgres, mysql, sqlite, mssql, oracle). Default: all.",
    )
    parser.addoption(
        "--kind",
        dest="sqlancer_kind",
        default=None,
        help="Comma-separated list of sqlancer kind subfolders to test "
             "(e.g. postgres-benign,postgres-traf-mismatch). Default: all.",
    )
    parser.addoption(
        "--from",
        dest="from_case",
        default=None,
        help="Start from this case id (alphabetical, inclusive). e.g. case_000100",
    )
    parser.addoption(
        "--upto",
        dest="upto_case",
        default=None,
        help="Stop at this case id (alphabetical, inclusive). e.g. case_000999",
    )
    parser.addoption(
        "--limit",
        dest="sqlancer_limit",
        type=int,
        default=None,
        help="Maximum number of cases to run per (engine, kind) bucket.",
    )
    parser.addoption(
        "--sqlancer-mismatch-report",
        dest="sqlancer_mismatch_report",
        default="sqlancer_mismatches.json",
        help=(
            "Path to write JSON summary/details for SQLancer mismatches. "
            "Relative paths are resolved from pytest rootdir. Use an empty "
            "string to disable report writing."
        ),
    )


def pytest_configure(config):
    config._sqlancer_mismatches = []


def _counter_dict(counter):
    return dict(sorted(counter.items(), key=lambda item: item[0]))


def _mismatch_payload(mismatches):
    by_engine = Counter(item["engine"] for item in mismatches)
    by_kind = Counter(item["kind"] for item in mismatches)
    by_reason = Counter(item["reason"] for item in mismatches)
    by_engine_kind = Counter(f"{item['engine']}/{item['kind']}" for item in mismatches)

    return {
        "summary": {
            "total": len(mismatches),
            "by_engine": _counter_dict(by_engine),
            "by_kind": _counter_dict(by_kind),
            "by_reason": _counter_dict(by_reason),
            "by_engine_kind": _counter_dict(by_engine_kind),
        },
        "mismatches": mismatches,
    }


def _engine_report_path(report_path: Path, engine: str) -> Path:
    if report_path.name.startswith(f"{engine}-"):
        return report_path
    return report_path.with_name(f"{engine}-{report_path.name}")


def _write_mismatch_report(report_path: Path, mismatches):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(_mismatch_payload(mismatches), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def pytest_sessionfinish(session, exitstatus):
    report_opt = session.config.getoption("sqlancer_mismatch_report")
    mismatches = getattr(session.config, "_sqlancer_mismatches", [])

    if report_opt:
        report_path = Path(report_opt)
        if not report_path.is_absolute():
            report_path = Path(session.config.rootpath) / report_path
        if mismatches:
            by_engine = {}
            for item in mismatches:
                by_engine.setdefault(item["engine"], []).append(item)
            for engine, engine_mismatches in by_engine.items():
                _write_mismatch_report(
                    _engine_report_path(report_path, engine),
                    engine_mismatches,
                )
        else:
            _write_mismatch_report(report_path, mismatches)


def pytest_collection_modifyitems(config, items):
    engines_opt = config.getoption("sqlancer_engines")
    kinds_opt = config.getoption("sqlancer_kind")
    from_case = config.getoption("from_case")
    upto_case = config.getoption("upto_case")
    limit = config.getoption("sqlancer_limit")

    if (engines_opt is None and kinds_opt is None and from_case is None
            and upto_case is None and limit is None):
        return

    engines = {e.strip() for e in engines_opt.split(",")} if engines_opt else None
    kinds = {k.strip() for k in kinds_opt.split(",")} if kinds_opt else None
    seen: dict[tuple[str, str], int] = {}
    selected = []

    for item in items:
        if not (hasattr(item, "callspec") and "kind" in item.callspec.params
                and "engine_name" in item.callspec.params):
            selected.append(item)
            continue

        engine = item.callspec.params["engine_name"]
        kind = item.callspec.params["kind"]
        case_name = item.callspec.params["yaml_path"].stem

        if engines is not None and engine not in engines:
            continue
        if kinds is not None and kind not in kinds:
            continue
        if from_case and case_name < from_case:
            continue
        if upto_case and case_name > upto_case:
            continue
        if limit is not None:
            key = (engine, kind)
            n = seen.get(key, 0)
            if n >= limit:
                continue
            seen[key] = n + 1

        selected.append(item)

    items[:] = selected
    if engines is not None:
        leaked = {
            item.callspec.params["engine_name"]
            for item in items
            if hasattr(item, "callspec")
            and "engine_name" in item.callspec.params
            and item.callspec.params["engine_name"] not in engines
        }
        if leaked:
            raise RuntimeError(
                f"SQLancer --engine filter leaked items for engines: {sorted(leaked)}"
            )
