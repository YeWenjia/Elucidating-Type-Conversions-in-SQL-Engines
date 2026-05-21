# A Formal Framework for Typing and Cast Semantics in SQL Engines

## Setup

We recommend using PyCharm to run.

1. Install Python 3.12 and select it as the environment in PyCharm.
2. Install packages listed in `requirements.txt`.
3. Install the target DBMS locally (SQLite, MySQL, PostgreSQL, MSSQL, Oracle).
4. Create tables in each engine using the scripts in the `datasql/` folder. Files whose names end with `_null` include `NULL` values.
5. Fill in the username, password, and other connection settings in `test/engines/config.yml`.
6. Run the engine tests in `test/engines/`: `psql_testing.py`, `mysql_testing.py`, `sqlite_testing.py`, `mssql_testing.py`, `oracle_testing.py`.

## Quick reference

```bash
# Spider
python -m pytest test/spider/test_spider_folders.py -v
python -m pytest test/spider/test_spider_folders.py -v -k 'activity_1/0005' -s

# Per-feature unit tests
python -m unittest test.features.test_aggregation.TestAggregation.test_having_aggregate_not_in_select -v

# Engine tests
python -m unittest test.engines.psql_testing.TestPostgres -v
python -m unittest test.engines.psql_testing.TestPostgres.test_join_0 -v

# Paper query audit
python test/paper_queries/run_paper_queries.py --engine sqlite
python test/paper_queries/run_paper_queries.py --engine all --config test/engines/config.yml
```

## Paper query audit

`test/paper_queries/` contains a manifest-driven audit for the SQL queries whose DBMS behavior is asserted in the paper, especially Table 1 and the examples in Section 4.

Run the SQLite-only audit, which needs no external server:

```bash
python test/paper_queries/run_paper_queries.py --engine sqlite
```

Run the audit against all configured DBMSs:

```bash
python test/paper_queries/run_paper_queries.py --engine all --config test/engines/config.yml
```

The script recreates the paper's `R(A,B)` table before running the selected queries. For non-SQLite engines it uses the same connector packages and config style as the validation tests in `test/engines`.

## Spider benchmark

To run a specific spider case against a single engine, prefix the `-k` filter with the engine name (`postgres`, `mysql`, `sqlite`, `mssql`, `oracle`). Test IDs follow `{engine}_{folder}/{yaml_stem}`:

```bash
python -m pytest test/spider/test_spider_folders.py -k "mysql_products_for_hire/0006" -v -s
python -m pytest test/spider/test_spider_folders.py -k "oracle_music_1/0016" -v -s
```

To run all spider benchmarks against a single engine, filter with just the engine name:

```bash
python -m pytest test/spider/test_spider_folders.py -k mssql -v
python -m pytest test/spider/test_spider_folders.py -k oracle  -v
```

## Calcite benchmark

`benchmarks/calcite/calcite2.jsonlines` contains 397 benchmark entries from Apache Calcite, each with a pair of semantically equivalent SQL queries (Calcite's rewrite-rule corpus). All entries share a single schema (`EMP`, `DEPT`, `BONUS`, `EMPNULLABLES`, `EMPNULLABLES_20`, `EMP_B`), populated once per test session with canonical SCOTT/EMP fixture data from `test/calcite/seed_data.py`. Each query in each pair produces one test case (794 total), comparing the interpreter's result against Postgres.

The first run creates the `traf_calcite` database, a `calcite` schema inside it, and seeds the tables. The Postgres user in `test/config.yml` needs `CREATEDB` permission (or create the database beforehand).

### Run the full suite

```bash
pytest test/calcite/ -v                              # default
pytest test/calcite/ --calcite-engine=postgres -v
pytest test/calcite/ --calcite-engine=sqlite   -v
pytest test/calcite/ --calcite-engine=mysql    -v
pytest test/calcite/ --calcite-engine=mssql    -v
pytest test/calcite/ --calcite-engine=oracle   -v
```

### Run a single entry

Pair index and side (`0` or `1`):

```bash
python -m pytest test/calcite/test_calcite_pairs.py -k "calcite-012_0" -v -s
```

Run both queries of a given pair:

```bash
python -m pytest test/calcite/test_calcite_pairs.py -k "calcite-012" -v
```

Per-engine single-entry examples:

```bash
pytest test/calcite/ -k "mssql-calcite-148_0"  -v
pytest test/calcite/ -k "mysql-calcite-385_0"  -v
pytest test/calcite/ -k "oracle-calcite-385_0" -v
```

## SQLancer benchmark

### Run the full suite

```bash
pytest test/sqlancer/ -v

pytest test/sqlancer/ --engine=postgres -v
pytest test/sqlancer/ --engine=sqlite   -v
pytest test/sqlancer/ --engine=mysql    -v
pytest test/sqlancer/ --engine=mssql    -v
pytest test/sqlancer/ --engine=oracle   -v
```

### Filter by `--kind`

The `--kind` flag filters by failure category: `traf-mismatch`, `benign`, `both-fail`, `traf-crash`, `dbms-fail`.

**Postgres**
```bash
pytest test/sqlancer/ --engine=postgres --kind=traf-mismatch -v
pytest test/sqlancer/ --engine=postgres --kind=benign        -v
pytest test/sqlancer/ --engine=postgres --kind=both-fail     -v
pytest test/sqlancer/ --engine=postgres --kind=traf-crash    -v
pytest test/sqlancer/ --engine=postgres --kind=dbms-fail     -v
```

**SQLite**
```bash
pytest test/sqlancer/ --engine=sqlite --kind=traf-mismatch -v
pytest test/sqlancer/ --engine=sqlite --kind=benign        -v
pytest test/sqlancer/ --engine=sqlite --kind=both-fail     -v
pytest test/sqlancer/ --engine=sqlite --kind=traf-crash    -v
pytest test/sqlancer/ --engine=sqlite --kind=dbms-fail     -v
```

**MySQL**
```bash
pytest test/sqlancer/ --engine=mysql --kind=traf-mismatch -v
pytest test/sqlancer/ --engine=mysql --kind=benign        -v
pytest test/sqlancer/ --engine=mysql --kind=both-fail     -v
pytest test/sqlancer/ --engine=mysql --kind=traf-crash    -v
pytest test/sqlancer/ --engine=mysql --kind=dbms-fail     -v
```

**Oracle**
```bash
pytest test/sqlancer/ --engine=oracle --kind=traf-mismatch -v
pytest test/sqlancer/ --engine=oracle --kind=benign        -v
pytest test/sqlancer/ --engine=oracle --kind=both-fail     -v
pytest test/sqlancer/ --engine=oracle --kind=traf-crash    -v
pytest test/sqlancer/ --engine=oracle --kind=dbms-fail     -v
```

**MSSQL**
```bash
pytest test/sqlancer/ --engine=mssql --kind=traf-mismatch -v
pytest test/sqlancer/ --engine=mssql --kind=benign        -v
pytest test/sqlancer/ --engine=mssql --kind=both-fail     -v
pytest test/sqlancer/ --engine=mssql --kind=traf-crash    -v
pytest test/sqlancer/ --engine=mssql --kind=dbms-fail     -v
```

### Single-case examples

```bash
pytest test/sqlancer/ -k "mssql_benign/case_000175"        -v
pytest test/sqlancer/ -k "mssql_traf-crash/case_000125"    -v
pytest test/sqlancer/ -k "oracle_traf-mismatch/case_000020" -v
pytest test/sqlancer/ -k "oracle_both-fail/case_000643"    -v
pytest test/sqlancer/ -k "oracle_dbms-fail/case_000274"    -v
pytest test/sqlancer/ -k "oracle_dbms-fail/case_000370"    -v
pytest test/sqlancer/ -k "sqlite_traf-crash/case_000010"   -v
```

### Mismatch reports

```bash
pytest test/sqlancer/ --engine=postgres --sqlancer-mismatch-report reports/sqlancer.json
```
