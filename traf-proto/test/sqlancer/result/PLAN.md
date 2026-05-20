# SQLancer mismatch triage — MSSQL + Oracle

Scope: `test/sqlancer/result/mssql-sqlancer_mismatches.json` (187 cases) and
`test/sqlancer/result/oracle-sqlancer_mismatches.json` (27 cases). Both files
report `kind=both-fail` only: the original benchmark labels these as failing
under PostgreSQL; the mismatch is between the interpreter and the rewritten
query that MSSQL or Oracle accept.

Filters applied per request:

- Skip anything already documented in [PROBLEMS.md](../../../PROBLEMS.md).
- Skip MSSQL `22003` integer-overflow engine errors.
- Skip MSSQL `42000` "Incorrect syntax" engine errors.

The instruction "errors on candidate types are solvable" was originally
misread as "skip them". The intent was the opposite — treat them as
**actionable** because they have a clean fix. See §2.5.

## 1. `engine_error_only` (priority bucket)

| Case | Engine error | Decision |
|------|--------------|----------|
| `case_000607` | `[42000] Incorrect syntax near the keyword 'NOT'` | skip (syntax) |
| `case_003098` | `[22003] '9223372036854775807' overflowed an int column` | skip (overflow) |
| `case_003105` | `[22003] '9223372036854775807' overflowed an int column` | skip (overflow) |
| `case_003109` | `[22003] '9223372036854775807' overflowed an int column` | skip (overflow) |
| `case_005682` | `[22003] '-9223372036854775808' overflowed an int column` | skip (overflow) |
| `case_005684` | `[22003] '-9223372036854775808' overflowed an int column` | skip (overflow) |
| `case_005685` | `[22003] '-9223372036854775808' overflowed an int column` | skip (overflow) |
| `case_006439` | `[22003] '9223372036854775807' overflowed an int column` | skip (overflow) |
| `case_006477` | `[22003] '-9223372036854775808' overflowed an int column` | skip (overflow) |

Result: every `engine_error_only` case falls into a skip category. No
interpreter change is required for this bucket. Oracle has zero
`engine_error_only` cases.

## 2. Remaining actionable buckets

After the skips above, the actionable population is dominated by one root
cause:

- MSSQL `interpreter_error_only` and `mssql_rewrite_folded_interpreter_error`:
  ~150 cases with `interpreter_error: "cast fails <junk> to Int"`.
- Oracle `interpreter_error_only`: 25 cases with
  `interpreter_error: "cast fails <junk> to Real"`.
- Two residual cases:
  - Oracle `case_005573` and MSSQL line 3261: Python error
    `'<' not supported between instances of 'NoneType' and 'NoneType'`.
  - Oracle `case_000510`: `result_mismatch` (interpreter returns 8 rows,
    Oracle returns 0) — not a cast-failure case.

### 2.1 Root cause of "cast fails X to Int/Real"

When a comparison resolves `SString` against `ZType`/`RType`, the typechecker
inserts an implicit cast on the string operand. At runtime the cast is
performed eagerly per row by:

- [interpreter/syntax/engine/Mssql.py:211-222](../../../interpreter/syntax/engine/Mssql.py#L211-L222)
  — `SString` → `ZType`, raises `Exception` on `int(...)` failure.
- [interpreter/syntax/engine/Mssql.py:223-230](../../../interpreter/syntax/engine/Mssql.py#L223-L230)
  — `SString` → `RType`, raises on `float(...)` failure.
- [interpreter/syntax/engine/Oracle.py:213-244](../../../interpreter/syntax/engine/Oracle.py#L213-L244)
  — `SString` → `ZType`, raises on `int(round(float(...)))` failure.
- [interpreter/syntax/engine/Oracle.py:245-252](../../../interpreter/syntax/engine/Oracle.py#L245-L252)
  — `SString` → `RType`, raises on `float(...)` failure.

The engines never observe the failure because the rewritten SQL wraps the
comparison in patterns the optimizer folds:

- `((P) IS NOT NULL) IS NOT NULL` collapses to `1 = 1` (MSSQL
  `mssql_rewrite_folded_interpreter_error`, e.g. `case_000598`).
- `CASE WHEN p THEN 1 WHEN NOT p THEN 0 ELSE NULL END` lets the engine return
  `NULL` for the row whose strict cast would have failed, propagating
  `NULL` up the boolean tree so the row is dropped from `WHERE`.

The interpreter does not short-circuit these patterns, so the eager cast
errors instead of returning `NULL`.

### 2.2 Proposed change — lenient string→number cast for MSSQL and Oracle

Convert the four `raise` sites above into `BValue(None)` returns so that a
failed numeric cast yields SQL `NULL` at the row level. `NULL` then
propagates through the surrounding comparison/`CASE`/`IS NULL` chain and the
row is filtered out by `WHERE`, matching the engine's observed result set.

Sketch (MSSQL; mirror for Oracle):

```python
case (SString(), ZType()):
    if e.v == '':
        v = Natural(0)
    else:
        try:
            v = Natural(int(e.v))
        except (ValueError, TypeError):
            return BValue(None)   # was: raise Exception(...)
    v.unknown = t.tag == 'Unknown'
    return v
case (SString(), RType()):
    try:
        v = Real(float(e.v))
    except (ValueError, TypeError):
        return BValue(None)       # was: raise Exception(...)
    v.unknown = t.tag == 'Unknown'
    return v
```

Where to apply:

- [interpreter/syntax/engine/Mssql.py:211-230](../../../interpreter/syntax/engine/Mssql.py#L211-L230)
- [interpreter/syntax/engine/Oracle.py:213-252](../../../interpreter/syntax/engine/Oracle.py#L213-L252)

Do not apply to:

- Postgres ([Postgres.py:218](../../../interpreter/syntax/engine/Postgres.py#L218),
  [Postgres.py:271](../../../interpreter/syntax/engine/Postgres.py#L271)) — Postgres
  rejects this comparison at typecheck and is unaffected by the rewrite.
- MySQL ([Mysql.py:282](../../../interpreter/syntax/engine/Mysql.py#L282)) —
  MySQL's coercion silently returns `0` for unparseable strings; the existing
  behavior in that file should keep the MySQL-specific rule (return `0`,
  not `NULL`).
- SQLite ([Sqlite.py:218](../../../interpreter/syntax/engine/Sqlite.py#L218),
  [Sqlite.py:316](../../../interpreter/syntax/engine/Sqlite.py#L316)) —
  SQLite stores values with their original affinity; not in scope for these
  two result files.

Trade-off: this introduces a soft FN risk on queries where MSSQL/Oracle
actually do raise a strict-cast error on real data. The 9
`engine_error_only` overflow cases listed above are an example; the new
behavior would mask them. They are already filtered (overflow is a separate
22003 path, not the `int()` path being patched), so this concern does not
materialize for the current corpus.

Expected impact: clears ~150 MSSQL cases and ~25 Oracle cases in a single
edit. Worth running the SQLancer regression after the change and counting
the new `by_reason` distribution before deciding whether the trade-off is
acceptable.

### 2.3 `'<' not supported between instances of 'NoneType' and 'NoneType'`

- Oracle `case_005573` (`SELECT … WHERE ((((((NULL)<=(NULL)))<=(1788027010))) IS NULL)`).
- The same family appears in the MSSQL file around line 3261.

The runtime path that evaluates `<=` is reaching Python's `<` operator with
both operands `None`. Per SQL semantics any comparison involving `NULL`
yields `NULL`, not an error.

Action: add an early `None`-guard at the comparison apply sites. Oracle
already has one at [Oracle.py:308-312](../../../interpreter/syntax/engine/Oracle.py#L308-L312)
for `apply`, but the failure comes from the `<=` synthesis (the `<` branch
inside `≤ ≡ < or =`). Trace the failing call and add the same `None`
short-circuit before invoking `<`. Run the two failing cases under
`pytest test/sqlancer -k case_005573 -v -s` to confirm.

### 2.4 Oracle `case_000510` — `result_mismatch`

```sql
SELECT * FROM database0_t0, database0_t1
WHERE ((((((-953827765) LIKE (database0_t1.c0))
        OR (((database0_t1.c1) IS NOT NULL)))) IS NULL);
```

Interpreter returns 8 rows; Oracle returns 0.

`OR` with one operand `IS NOT NULL` is never `NULL` in Oracle:
`x OR (y IS NOT NULL)` is `True` whenever the second disjunct is `True`, and
`(y IS NOT NULL)` is itself never `NULL`. So the outer `IS NULL` should
always be `False`, agreeing with Oracle's empty result.

Action: audit the interpreter's `OR` truth table for the case
`NULL OR True = True` and `NULL OR False = NULL`. The likely defect is that
`(N LIKE c0)` returning `NULL` is being treated as `NULL` after `OR True`,
instead of being absorbed. Inspect
[interpreter/Runtime.py](../../../interpreter/Runtime.py) `Or`/`OrOp`
evaluation; expect a missing `True`-absorbs-NULL branch in Oracle's
short-circuit path. Cross-check against the
"NULL comparison elimination" note in
[PROBLEMS.md:223](../../../PROBLEMS.md#L223).

### 2.5 MSSQL "No best candidate for the given types ?, String" — DONE

29 MSSQL cases (16 with order `?, String`, 13 with `String, ?`). Zero Oracle.

Root cause in [Mssql.py:107-122](../../../interpreter/syntax/engine/Mssql.py#L107-L122).
The candidate list for `<` and `=` enumerates 12 `FuncType` entries covering
all pairings except `(SType, UType)` and `(UType, SType)`. For an input pair
`(UType, SType)` the cost function ties two candidates at cost 1:
`(SType, SType) = cost(U,S)+cost(S,S) = 1+0` and
`(UType, ZType) = cost(U,U)+cost(S,Z) = 0+1`. `best_candidate` raises
"No best candidate" on the tie at
[Mssql.py:150](../../../interpreter/syntax/engine/Mssql.py#L150).

Fix (applied): add `(SType, UType)` and `(UType, SType)` candidates to `<`
and `=` in [Mssql.py:107-122](../../../interpreter/syntax/engine/Mssql.py#L107-L122).
With the new candidates, `(U, S)` resolves to cost 0 against
`(UType, SType)` and wins unambiguously. At runtime, the `apply` site
already short-circuits to `BValue(None)` when either operand is `None`
([Mssql.py:275-276](../../../interpreter/syntax/engine/Mssql.py#L275-L276)),
so no runtime change is needed.

Verification: all 29 cases now pass; a 30-case random sample of unrelated
mismatches showed zero regressions and four bonus fixes where the candidate
ambiguity had been masking another typecheck issue.

Oracle was unaffected because its `cost` table happens to give
`cost(SType, UType) = 2` (default), so the `(S, S)` candidate already wins
unambiguously at cost 1 on `(UType, SType)` input — no tie there.

## 3. Suggested execution order

1. **2.3** — DONE.
2. **2.5** — DONE.
3. **2.4** — Oracle `result_mismatch`. Documented as a §6.3.4 known
   divergence; no interpreter change recommended (see plan body).
4. **2.2** — the high-impact lenient-cast change. Land last because it
   alters semantics for two engines and needs a full SQLancer rerun plus
   diffing of `by_reason` totals to confirm no new FN inflation.

## 4. Verification commands

```bash
python -m pytest test/sqlancer -k 'case_005573 or case_000510' -v -s

python test/sqlancer/run_case.py mssql case_000598
python test/sqlancer/run_case.py oracle case_001147

python -m pytest test/sqlancer -v
```

After step 2.2 lands, regenerate the two mismatch JSON files and compare
the `summary.by_reason` counts before vs. after.
