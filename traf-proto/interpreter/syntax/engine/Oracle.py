import numpy as np
from interpreter import Runtime
from interpreter.syntax.expression.Op import *
from interpreter.Typechecker import *
from interpreter.Runtime import *
from interpreter.AbstractOps import *
import re

class OracleOps(AbstractOps):
    use_truth_value_for_logical_ops = True

    def truth_value(self, v):
        value = v.erase()
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, Decimal)):
            return value != 0
        if isinstance(value, str):
            # Match Postgres `parse_bool`: trim whitespace then accept any
            # prefix-abbreviated form of true/false/yes/no plus on/off/0/1.
            text = value.strip().lower()
            if text in ("t", "tr", "tru", "true", "y", "ye", "yes", "on", "1"):
                return True
            if text in ("", "f", "fa", "fal", "fals", "false", "n", "no", "of", "off", "0"):
                return False
            raise ValueError(f"invalid boolean literal: {value}")
        return bool(value)

    def clean(self, T: RelationType) -> RelationType:
        return T

    def ty(self, e: Expression):
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match e:
            case Real():
                return RType()
            case Natural():
                return ZType()
            case SString():
                return SType()
            case Boolean():
                return BType()
            case Nullv():
                return UType()
            case DateTime():
                return DTType()
            case _:
                raise TypeError(f"Type not found: {e}")

    def uicast(self, e, t1, t2):
        match t1:
            case UType():
                return True
            case _:
                return self.type_implicit_cast(t1, t2)

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        t3s = self.ty_op(op)
        t = self.best_candidate(t1, t2, t3s)
        if self.explicit_cast_feasibility(e1, t1, t.dom[0]) and self.explicit_cast_feasibility(e2, t2, t.dom[1]):
            return t
        else:
            raise TypeError(f"resolve fails: {e1}, {t1}, {e2}, {t2}")

    def resolve_agg_func(self, e: Expression, t: ValueType, agg_func: str) -> FuncType:
        # Oracle collapses all numeric types to NUMBER; OracleOps models numerics as RType.
        match agg_func:
            case "COUNT":
                return FuncType(t, RType())
            case "SUM" | "AVG":
                if isinstance(t, (ZType, RType, SType)):
                    return FuncType(RType(), RType())
                elif isinstance(t, UType):
                    return FuncType(t, UType())
                else:
                    raise TypeError(f"{agg_func} requires numeric type, got {t}")
            case "MAX" | "MIN":
                return FuncType(t, t)
            case _:
                raise Exception(f"Unsupported aggregate function: {agg_func}")

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                # No (BType, BType) candidate: the Oracle test rewrite wraps
                # every comparison operand that's a boolean expression in a
                # `CASE WHEN ... THEN 1 ELSE 0 END` numeric form, so engine
                # comparisons see numeric. Force the interpreter through the
                # same numeric path via (RType, RType).
                return [FuncType([RType(), RType()], BType()), FuncType([SType(), SType()], BType()), FuncType([UType(), UType()], BType()), FuncType([DTType(), DTType()], BType())]
            case "=":
                return [FuncType([RType(), RType()], BType()), FuncType([SType(), SType()], BType()), FuncType([UType(), UType()], BType()), FuncType([DTType(), DTType()], BType())]
            case "LIKE":
                return [FuncType([SType(), SType()], BType())]
            case "+" | "-" | "*" | "/":
                return [FuncType([RType(), RType()], RType()), FuncType([UType(), UType()], UType())]
            case _:
                raise Exception(f"Operation not found: {op}")

    def best_candidate(self, t1, t2, t3s):
        ms = list(map(lambda x: self.cost(t1, x.dom[0]) + self.cost(t2, x.dom[1]), t3s))
        min_val = min(ms)
        if ms.count(min_val) == 1:
            argmin = ms.index(min_val)
            candidate = t3s[argmin]
            return candidate
        else:
            raise TypeError(f"No best candidate for the given types {t1}, {t2}")

    def cost(self, t1, t2) -> int:
        match (t1, t2):
            case (t1, t2) if t1 == t2:
                return 0
            case (ZType(), RType()):
                return 0
            case (BType(), RType()):
                # The Oracle test rewrite wraps every BOOL comparison operand
                # in `CASE WHEN ... THEN 1 ELSE 0 END` (numeric), so the engine
                # always sees `BOOL <op> X` as `NUMBER <op> X`. Make BOOL→REAL
                # the cheapest coercion here so the interpreter picks the same
                # numeric path; otherwise (BType, BType) wins via cost 0+1 and
                # we diverge from the engine on `Bool <op> Int/Real`.
                return 0
            case (SType(), RType()) | (UType(), _):
                return 1
            case (ZType(), BType()) | (RType(), BType()) | (SType(), BType()):
                # Mixed bool comparisons that don't have a numeric candidate
                # (only `(BType, BType)` candidate in ty_op) should still be
                # cheap to convert towards bool to avoid "no best candidate".
                return 1
            case _:
                return 2

    def biconv(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType):
        if self.uicast(e1, t1, t2):
            return t2
        elif self.uicast(e2, t2, t1):
            return t1
        else:
            raise TypeError(f"biconv fails {e1}, {t1}, {e2}, {t2}")

    def explicit_cast_feasibility(self, e: Expression, tp: ValueType, t: ValueType):
        return True


    def cast(self, e: Expression, t: ValueType):
        """
        This function represents an explicit cast in the paper. It is used to cast a value to a specific type.
        """
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        # Oracle treats the empty string as NULL, so any cast from '' is NULL
        # rather than a parse-attempt failure.
        if isinstance(e, SString) and e.v == '':
            return Nullv(None)
        match (e, t):
            case (Nullv(), _):
                return e
            case (Real(), RType()):
                if e.v == int(e.v):
                    v = Real(int(e.v))
                    v.unknown = t.tag == 'Unknown'
                    return v
                else:
                    v = Real(Decimal(e.v))
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (v, t) if self.ty(v) == t:
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), RType()):
                v = Real(e.v)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Boolean(), RType()):
                # Oracle treats BOOLEAN as 1/0 when coerced to numeric.
                v = Real(1.0 if e.v else 0.0)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Boolean(), ZType()):
                v = Natural(1 if e.v else 0)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), BType()) | (Real(), BType()):
                # Oracle 23c truthy conversion: zero → FALSE, anything else → TRUE.
                v = Boolean(e.v != 0)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), ZType()):
                if e.v >= 0:
                    i = int(e.v + Decimal('0.5'))
                    v = Natural(i)
                    v.unknown = t.tag == 'Unknown'
                    return v
                else:
                    i = int(e.v - Decimal('0.5'))
                    v = Natural(i)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (Natural(), SType()) | (Boolean(), SType()):
                v = SString(str(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), SType()):
                if e.v == int(e.v):
                    v = SString(str(int(e.v)))
                    v.unknown = t.tag == 'Unknown'
                    return v
                else:
                    v = SString(str(e.v))
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), ZType()):
                try:
                    v = float(e.v)
                    vv = int(v)
                    d = v - vv
                    if d == 0:
                        r = Natural(vv)
                        r.unknown = t.tag == 'Unknown'
                        return r
                    elif d > 0 and d < 0.5:
                        r = Natural(vv)
                        r.unknown = t.tag == 'Unknown'
                        return r
                    elif d > 0 and d >= 0.5:
                        r = Natural(vv+1)
                        r.unknown = t.tag == 'Unknown'
                        return r
                    elif d < 0 and -d < 0.5:
                        r = Natural(vv)
                        r.unknown = t.tag == 'Unknown'
                        return r
                    elif d < 0 and -d >= 0.5:
                        r = Natural(vv-1)
                        r.unknown = t.tag == 'Unknown'
                        return r
                except ValueError:
                    raise Exception(f"cast fails {e} to {t}")
            case(SString(), RType()):
                try:
                    r = float(e.v)
                    v = Real(r)
                    v.unknown = t.tag == 'Unknown'
                    return v
                except:
                    raise Exception(f"cast fails {e} to {t}")
            case (SString(), BType()):
                # Reuse the same Postgres-style truth-literal rules as
                # truth_value so the typecheck-time cast matches the runtime
                # WHERE-truth check (avoids 'no best candidate' resolutions
                # erroring at apply-time on otherwise-acceptable strings).
                text = e.v.strip().lower()
                if text in ("t", "tr", "tru", "true", "y", "ye", "yes", "on", "1"):
                    v = Boolean(True)
                elif text in ("f", "fa", "fal", "fals", "false", "n", "no", "of", "off", "0"):
                    v = Boolean(False)
                else:
                    raise TypeError(f"cast fails {e} to {t}")
                v.unknown = t.tag == 'Unknown'
                return v
            case (DateTime(), DTType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (DateTime(), SType()):
                # Oracle implicit DATE/TIMESTAMP -> string conversion is NLS-dependent
                # and does not default to ISO 8601. Use an Oracle-like textual form so
                # LIKE '2016%' does not spuriously match datetime values.
                dt = e.v
                if hasattr(dt, "strftime"):
                    if (
                        getattr(dt, "hour", 0) == 0 and
                        getattr(dt, "minute", 0) == 0 and
                        getattr(dt, "second", 0) == 0 and
                        getattr(dt, "microsecond", 0) == 0
                    ):
                        s = dt.strftime("%d-%b-%y").upper()
                    else:
                        s = dt.strftime("%d-%b-%y %I.%M.%S.%f %p").upper()
                else:
                    s = str(dt)
                v = SString(s)
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), DTType()):
                from datetime import datetime
                try:
                    v = DateTime(datetime.strptime(e.v, '%Y-%m-%d %H:%M:%S'))
                except ValueError:
                    try:
                        v = DateTime(datetime.strptime(e.v, '%Y-%m-%d'))
                    except ValueError:
                        v = DateTime(e.v)
                v.unknown = t.tag == 'Unknown'
                return v
            case (v, UType()):
                return v
        raise TypeError(f"cast fails {e} to {t}")

    def insert(self, e: Expression, t: ValueType, op: str) -> Expression:
        return Ascr(e, t)

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
        a, b = v1.erase(), v2.erase()
        # Oracle treats the empty string as NULL.
        if a is None or b is None or (isinstance(a, str) and a == '') or (isinstance(b, str) and b == ''):
            return BValue(None)
        numeric = (Decimal, float, int)
        both_numeric = isinstance(a, numeric) and isinstance(b, numeric) and not isinstance(a, bool) and not isinstance(b, bool)
        match op:
            case "<":
                return BValue(a < b)
            case "=":
                # Use tolerance for numeric types — 32-bit BINARY_FLOAT storage or
                # binary<->decimal conversions can introduce ~1e-7 drift that would
                # cause strict equality to miss otherwise-matching rows.
                if both_numeric and (isinstance(a, (Decimal, float)) or isinstance(b, (Decimal, float))):
                    return BValue(bool(np.isclose(float(a), float(b))))
                return BValue(a == b)
            case "LIKE":
                import re
                # Convert SQL LIKE pattern to regex
                pattern = str(v2.erase())
                # Replace % and _ with placeholders to protect them during escaping
                pattern = pattern.replace('%', '\x00')  # Use null char as placeholder for %
                pattern = pattern.replace('_', '\x01')  # Use SOH char as placeholder for _
                # Escape special regex chars
                pattern = re.escape(pattern)
                # Replace placeholders with regex equivalents
                pattern = pattern.replace('\x00', '.*')  # % matches any sequence
                pattern = pattern.replace('\x01', '.')   # _ matches single char
                # Match the entire string
                pattern = '^' + pattern + '$'
                result = re.match(pattern, str(v1.erase()), re.DOTALL) is not None
                return BValue(result)
            case "+":
                r = v1.erase() + v2.erase()
                return BValue(r)
            case "-":
                return BValue(v1.erase() - v2.erase())
            case "*":
                return BValue(v1.erase() * v2.erase())
            case "/":
                return BValue(v1.erase() / v2.erase())
            case _:
                raise TypeError(f"operation {op} not support")

    def check_optimization(self):
        return True

    def check_isnull_null(self):
        return True

    def isnull_res(self, v):
        # Oracle treats the empty string as NULL.
        if v.v is None or (isinstance(v.v, str) and v.v == ''):
            return BValue(True)
        return BValue(False)


class Oracle(Engine):
    typechecker = Typechecker(OracleOps())

    run = Runtime(OracleOps())

    def __init__(self):
        self.tag = "Oracle"

    def __str__(self):
        return "Oracle"

    def infer_schema(self, connection):
        """Infer schema from Oracle database using ALL_TAB_COLUMNS."""
        cursor = connection.cursor()
        schema = {}

        cursor.execute("""
            SELECT table_name FROM user_tables
            WHERE table_name IN ('TA','TB','TC')
            ORDER BY table_name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        for table_name in tables:
            cursor.execute("""
                SELECT column_name, data_type
                FROM user_tab_columns
                WHERE table_name = :1
                ORDER BY column_id
            """, (table_name,))

            columns = cursor.fetchall()
            name_types = []

            for col_name, data_type in columns:
                interpreter_type = self._map_oracle_type(data_type)
                name_types.append(NameType(col_name.lower(), interpreter_type))

            schema[table_name] = RelationType(name_types)

        cursor.close()
        return schema

    def _map_oracle_type(self, data_type: str):
        """Map Oracle data types to interpreter types."""
        data_type = data_type.upper()
        if data_type in ('NUMBER', 'INTEGER', 'SMALLINT', 'INT'):
            return ZType()
        elif data_type in ('FLOAT', 'BINARY_FLOAT', 'BINARY_DOUBLE'):
            return RType()
        elif data_type in ('DATE', 'TIMESTAMP') or data_type.startswith('TIMESTAMP'):
            return DTType()
        else:
            return SType()

    def comparev(self, v1, v2):
        if isinstance(v2, Decimal) and type(v1) == float:
            v2 = float(v2)
            return np.isclose(v1, v2)
        elif isinstance(v1, Decimal) and type(v2) == Decimal:
            result = np.isclose(float(v1), float(v2))
            return result
        elif isinstance(v1, Decimal) and type(v2) == float:
            v1 = float(v1)
            return np.isclose(v2, v1)
        elif type(v2) == float and type(v1) == float:
            return np.isclose(v1,v2)
        else:
            return v1 == v2
