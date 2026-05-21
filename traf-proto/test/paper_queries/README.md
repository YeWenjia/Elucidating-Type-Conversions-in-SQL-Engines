# Paper Query Audit

This directory contains a manifest-driven audit for the SQL queries whose DBMS
behavior is asserted in the paper, especially Table 1 and the examples in
Section 4.

Run the SQLite-only audit, which needs no external server:

```bash
python test/paper_queries/run_paper_queries.py --engine sqlite
```

Run the audit against all configured DBMSs:

```bash
python test/paper_queries/run_paper_queries.py --engine all --config test/engines/config.yml
```

The script recreates the paper's `R(A,B)` table before running the selected
queries. For non-SQLite engines it uses the same connector packages and config
style as the validation tests in `test/engines`.
