import json
from pathlib import Path

from interpreter.syntax.engine.Engine import Engine
from interpreter.queryGenerator import *
from interpreter.Runtime import Eta
import unittest

from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.Database import Database


# ---------------------------------------------------------------------------
# Experiment bookkeeping mixin
# ---------------------------------------------------------------------------
# Drop this into any TestEngine subclass to:
#   - count how many queries are statically rejected by the type system
#   - count how many well-typed queries pass / mismatch the real engine
#   - dump five JSON files per engine under experiment_results/
#
# A test class using the mixin must:
#   - set the class attribute `experiment_prefix` (e.g. "psql", "sqlite")
#   - inherit from `ExperimentMixin` BEFORE `TestEngine` so the override of
#     `compare_command` takes precedence.
#
# Pass / fail follows pure agreement: same outcome (rows OR both error) =
# pass; any disagreement = fail.
class ExperimentMixin:
    experiment_prefix: str = "engine"

    @classmethod
    def _init_experiment_state(cls):
        cls.experiment_stats = {
            "total": 0,
            "statically_rejected": 0,
            "well_typed": 0,
            "well_typed_matched": 0,
            "well_typed_mismatched": 0,
            "passed": 0,
            "failed": 0,
        }
        cls.experiment_all = []
        cls.experiment_passed = []
        cls.experiment_failed = []
        cls.experiment_mismatches = []
        cls.experiment_statically_rejected = []

    def compare_command(self, command: str, simplification=False, test_index=None):
        cls = type(self)
        if not hasattr(cls, "experiment_stats"):
            cls._init_experiment_state()
        cls.experiment_stats["total"] += 1

        statically_rejected = False
        runtime_error = False
        their_error = False
        interp_repr: str = ""
        engine_repr: str = ""
        mytable = None
        rows = []

        # 1. Parse + typecheck (separate from evaluation)
        parsed = None
        qp = None
        try:
            parsed = self.parse_command(command)
            TQ = self.engine.typechecker.typecheck_query(
                self.dbt, RelationType([]), parsed)
            qp = TQ[1]
        except Exception as e:
            statically_rejected = True
            cls.experiment_stats["statically_rejected"] += 1
            interp_repr = f"static-typecheck-error: {e}"

        # 2. Evaluate (only if well typed)
        if not statically_rejected:
            try:
                mytable = self.engine.run.run_query(self.db, Eta([], []), qp)
                interp_repr = (
                    f"{len(mytable.rows)} rows: "
                    + str([[v.erase() for v in r] for r in mytable.rows[:10]])
                )
            except Exception as e:
                runtime_error = True
                interp_repr = f"runtime-error: {e}"

        # 3. Run the real engine
        cur = self.conn.cursor()
        try:
            engine_cmd = (command.replace(";", "")
                          if self.engine.tag == "Oracle" else command)
            cur.execute(engine_cmd)
            rows = cur.fetchall()
            engine_repr = f"{len(rows)} rows: {rows[:10]}"
        except Exception as e:
            their_error = True
            engine_repr = f"engine-error: {e}"
        try:
            self.conn.rollback()
        except Exception:
            pass
        cur.close()

        # 4. Reconcile and classify
        interp_failed = statically_rejected or runtime_error
        if interp_failed and their_error:
            outcome = "both_failed"
        elif not interp_failed and not their_error:
            match = Engine().Compare(mytable.rows, list(rows), self.engine)
            outcome = "match" if match else "value_mismatch"
        elif interp_failed and not their_error:
            outcome = "interp_only_error"
        else:
            outcome = "engine_only_error"

        # 5. Record every query
        entry = {
            "test_name": getattr(self, "_testMethodName", None),
            "test_index": test_index,
            "query": command,
            "outcome": outcome,
            "statically_rejected": statically_rejected,
            "interpreter": interp_repr,
            "engine": engine_repr,
        }
        cls.experiment_all.append(entry)

        # Pass/fail = agreement.
        passed = outcome in {"match", "both_failed"}
        if passed:
            cls.experiment_stats["passed"] += 1
            cls.experiment_passed.append(entry)
        else:
            cls.experiment_stats["failed"] += 1
            cls.experiment_failed.append(entry)

        if statically_rejected:
            cls.experiment_statically_rejected.append(entry)
        else:
            cls.experiment_stats["well_typed"] += 1
            if outcome in {"match", "both_failed"}:
                cls.experiment_stats["well_typed_matched"] += 1
            else:
                cls.experiment_stats["well_typed_mismatched"] += 1
                cls.experiment_mismatches.append(entry)

        # Let unittest report the test as pass/fail (the `.` or `F` per query)
        # without printing per-query lines from inside the test body.
        self.assertTrue(
            passed,
            msg=f"outcome={outcome} | SQL: {command} | "
                f"interpreter={interp_repr} | engine={engine_repr}",
        )

    @classmethod
    def _dump_experiment_results(cls):
        if not hasattr(cls, "experiment_stats"):
            return
        out_dir = Path(__file__).parent / "experiment_results"
        out_dir.mkdir(exist_ok=True)
        prefix = cls.experiment_prefix
        spec = [
            (f"{prefix}_all_queries.json",          "queries",     cls.experiment_all),
            (f"{prefix}_statically_rejected.json",  "queries",     cls.experiment_statically_rejected),
            (f"{prefix}_passed.json",               "queries",     cls.experiment_passed),
            (f"{prefix}_failed.json",               "queries",     cls.experiment_failed),
            (f"{prefix}_mismatches.json",           "mismatches",  cls.experiment_mismatches),
        ]
        for fname, key, data in spec:
            with open(out_dir / fname, "w") as f:
                json.dump({"stats": cls.experiment_stats, key: data},
                          f, indent=2, default=str)

        s = cls.experiment_stats
        bar = "=" * 70
        print(f"\n{bar}\n  {prefix.upper()} EXPERIMENT SUMMARY\n{bar}")
        print(f"  Total queries:                {s['total']}")
        print(f"  Passed:                       {s['passed']}")
        print(f"  Failed:                       {s['failed']}")
        print(f"    - statically rejected:      {s['statically_rejected']}")
        print(f"    - well-typed mismatched:    {s['well_typed_mismatched']}")
        print(f"  Well-typed:                   {s['well_typed']}")
        print(f"    - matched engine:           {s['well_typed_matched']}")
        print(f"    - mismatched engine:        {s['well_typed_mismatched']}")
        print(f"  Output -> {out_dir}/{prefix}_*.json")
        print(bar)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.conn.close()
        except Exception:
            pass
        cls._dump_experiment_results()


SEP = "=" * 70
THIN = "-" * 70


class TestEngine(unittest.TestCase):
    db = Database({})
    dbt = {}

    stats = {
        'total_tests': 0,
        'our_error': 0,
        'their_error': 0,
        'compare_false': 0,
    }

    error_ids = {
        'our_error_ids': [],
        'their_error_ids': [],
        'compare_false_ids': []
    }

    lark = False

    @classmethod
    def populateDatabase(cls, use_decimal=True):
        cur = cls.conn.cursor()

        # Use automatic schema inference from database
        cls.dbt = cls.engine.infer_schema(cls.conn)

        # Dynamically generate cls.db from the inferred schema
        cls.db = Database({})
        for table_name, rel_type in cls.dbt.items():
            col_names = [name_type.name for name_type in rel_type.nametypes]
            col_list = ', '.join(col_names)
            query = f"SELECT {col_list} FROM {table_name}"

            cur.execute(query)
            rows = [list(r) for r in cur.fetchall()]
            for row in rows:
                for i, v in enumerate(row):
                    cv = BValue(v, use_decimal)
                    cv.unknown = False
                    row[i] = cv

            cls.db[table_name] = Table(col_names, rows)

        cur.close()

    def write_string_to_file(self, string, filename):
        with open(filename, 'a') as file:
            file.write(string + '\n')

    def parse_command(self, command: str):
        if not self.lark:
            parsed = sqlparse.parse(command)
            statement = parsed[0]
            query_object = self.parser.parse_select(statement)
            return query_object
        else:
            query_object = self.parser.parse(command)
            return query_object

    def compare_command(self, command: str, simplification=False, test_index=None):
        rows = []
        their_error = False
        our_error = False
        compare_result = True

        self.__class__.stats['total_tests'] += 1
        current_test_id = self.__class__.stats['total_tests']

        # Header
        print(f"\n{SEP}")
        test_label = f"Test #{current_test_id}"
        if test_index is not None:
            test_label += f" (index {test_index})"
        print(f"  {test_label}")
        print(SEP)
        print(f"  SQL: {command}")
        print(THIN)

        cur = self.conn.cursor()

        # Run in interpreter
        parsed = self.parse_command(command)
        mytable = []
        try:
            TQ = self.engine.typechecker.typecheck_query(self.dbt, RelationType([]), parsed)
            T = TQ[0]
            qp = TQ[1]
            mytable = self.engine.run.run_query(self.db, Eta([], []), qp)
            print(f"  Parsed:      {parsed}")
            print(f"  Type:        {T}")
            print(f"  Translation: {qp}")
            print(f"  Interpreter: {len(mytable.rows)} rows")
            for row in mytable.rows:
                vals = [v.erase() for v in row]
                print(f"    {vals}")
        except Exception as e:
            our_error = True
            print(f"  Interpreter ERROR: {e}")

        print(THIN)

        # Run in real engine
        try:
            if self.engine.tag == "Oracle":
                command = command.replace(";", "")
            cur.execute(command)
            column_names = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            print(f"  {self.engine.tag}: {len(rows)} rows  (columns: {column_names})")
            for row in rows:
                print(f"    {list(row)}")
        except Exception as e:
            print(f"  {self.engine.tag} ERROR: {e}")
            their_error = True
        self.conn.rollback()

        print(THIN)

        # Compare results
        if their_error and our_error:
            print(f"  Result: BOTH FAILED")
            assert our_error == their_error
        elif not their_error and not our_error:
            compare_result = Engine().Compare(mytable.rows, list(rows), self.engine)
            if compare_result:
                print(f"  Result: MATCH ({len(rows)} rows)")
            else:
                self.__class__.stats['compare_false'] += 1
                if test_index is not None:
                    self.__class__.error_ids['compare_false_ids'].append((current_test_id, test_index))
                else:
                    self.__class__.error_ids['compare_false_ids'].append(current_test_id)

                print(f"  Result: MISMATCH ({len(mytable.rows)} interpreter vs {len(rows)} engine)")
                # Print diff
                our_vals = [tuple(v.erase() for v in row) for row in mytable.rows]
                their_vals = [tuple(row) for row in rows]
                only_ours = [r for r in our_vals if r not in their_vals]
                only_theirs = [r for r in their_vals if r not in our_vals]
                if only_ours:
                    print(f"  Only in interpreter ({len(only_ours)}):")
                    for r in only_ours:
                        print(f"    + {r}")
                if only_theirs:
                    print(f"  Only in {self.engine.tag} ({len(only_theirs)}):")
                    for r in only_theirs:
                        print(f"    - {r}")
            assert compare_result
        else:
            if our_error and not their_error:
                self.__class__.stats['our_error'] += 1
                if test_index is not None:
                    self.__class__.error_ids['our_error_ids'].append((current_test_id, test_index))
                else:
                    self.__class__.error_ids['our_error_ids'].append(current_test_id)
                print(f"  Result: INTERPRETER FAILED (engine succeeded)")
            if their_error and not our_error:
                self.__class__.stats['their_error'] += 1
                if test_index is not None:
                    self.__class__.error_ids['their_error_ids'].append((current_test_id, test_index))
                else:
                    self.__class__.error_ids['their_error_ids'].append(current_test_id)
                print(f"  Result: ENGINE FAILED (interpreter succeeded)")
            assert our_error == their_error

        print(SEP)
        cur.close()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        total = cls.stats['total_tests']
        passed = total - cls.stats['our_error'] - cls.stats['their_error'] - cls.stats['compare_false']

        print(f"\n\n{'=' * 70}")
        print(f"  SUMMARY")
        print(f"{'=' * 70}")
        print(f"  Total:            {total}")
        print(f"  Passed:           {passed}")
        print(f"  Interpreter fail: {cls.stats['our_error']}")
        print(f"  Engine fail:      {cls.stats['their_error']}")
        print(f"  Mismatch:         {cls.stats['compare_false']}")
        print(f"{'=' * 70}")
        if cls.error_ids['our_error_ids']:
            print(f"\n  Interpreter failures ({len(cls.error_ids['our_error_ids'])}):")
            print(f"    {cls.error_ids['our_error_ids']}")
        if cls.error_ids['their_error_ids']:
            print(f"\n  Engine failures ({len(cls.error_ids['their_error_ids'])}):")
            print(f"    {cls.error_ids['their_error_ids']}")
        if cls.error_ids['compare_false_ids']:
            print(f"\n  Mismatches ({len(cls.error_ids['compare_false_ids'])}):")
            print(f"    {cls.error_ids['compare_false_ids']}")
        print(f"{'=' * 70}\n")
