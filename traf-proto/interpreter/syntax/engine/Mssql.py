import numpy as np
from interpreter import Runtime
from interpreter.syntax.expression.Op import *
from interpreter.Typechecker import *
from interpreter.Runtime import *
from interpreter.AbstractOps import *
import re


class MssqlOps(AbstractOps):
    def clean(self, T: RelationType) -> RelationType:
        return T

    def normalize_for_comparison(self, value):
        # Tables are created with Latin1_General_BIN2 (binary, case-sensitive,
        # NO PAD), so comparisons are by code point with no normalization.
        return value

    def truth_value(self, v):
        # MSSQL itself rejects non-boolean WHERE conditions, but our test
        # harness rewrites bare-string WHEREs using Postgres's truthiness
        # rules — match those rules here so the interpreter agrees with the
        # rewritten query MSSQL actually runs.
        from decimal import Decimal
        value = v.erase()
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, Decimal)):
            return value != 0
        if isinstance(value, str):
            text = value.strip().lower()
            if text in ("t", "tr", "tru", "true", "y", "ye", "yes", "on", "1"):
                return True
            if text in ("", "f", "fa", "fal", "fals", "false", "n", "no", "of", "off", "0"):
                return False
            raise ValueError(f"invalid boolean literal: {value}")
        return bool(value)

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
            case SType():
                return True
            case UType():
                return True
            case _:
                return self.type_implicit_cast(t1, t2)
        return False

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        t3s = self.ty_op(op)
        t = self.best_candidate(t1, t2, t3s)
        if self.explicit_cast_feasibility(e1, t1, t.dom[0]) and self.explicit_cast_feasibility(e2, t2, t.dom[1]):
            return t
        else:
            raise TypeError(f"resolve fails: {e1}, {t1}, {e2}, {t2}")

    def resolve_agg_func(self, e: Expression, t: ValueType, agg_func: str) -> FuncType:
        match agg_func:
            case "COUNT":
                return FuncType(t, ZType())
            case "SUM":
                if isinstance(t, ZType):
                    return FuncType(t, ZType())
                elif isinstance(t, RType):
                    return FuncType(t, RType())
                elif isinstance(t, UType):
                    return FuncType(t, UType())
                else:
                    raise TypeError(f"SUM requires numeric type, got {t}")
            case "AVG":
                # T-SQL: AVG on an integer column returns an integer (truncated)
                if isinstance(t, ZType):
                    return FuncType(t, ZType())
                elif isinstance(t, RType):
                    return FuncType(t, RType())
                elif isinstance(t, UType):
                    return FuncType(t, UType())
                else:
                    raise TypeError(f"AVG requires numeric type, got {t}")
            case "MAX" | "MIN":
                return FuncType(t, t)
            case _:
                raise Exception(f"Unsupported aggregate function: {agg_func}")

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType()), FuncType([UType(), UType()], BType()),
                        FuncType([DTType(), DTType()], BType()), FuncType([BType(), BType()], BType()),
                        FuncType([BType(), ZType()], BType()), FuncType([ZType(), BType()], BType()),
                        FuncType([ZType(), UType()], BType()), FuncType([UType(), ZType()], BType()),
                        FuncType([BType(), UType()], BType()), FuncType([UType(), BType()], BType()),
                        FuncType([SType(), UType()], BType()), FuncType([UType(), SType()], BType())]
            case "=":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType()), FuncType([UType(), UType()], BType()),
                        FuncType([DTType(), DTType()], BType()), FuncType([BType(), BType()], BType()),
                        FuncType([BType(), ZType()], BType()), FuncType([ZType(), BType()], BType()),
                        FuncType([ZType(), UType()], BType()), FuncType([UType(), ZType()], BType()),
                        FuncType([BType(), UType()], BType()), FuncType([UType(), BType()], BType()),
                        FuncType([SType(), UType()], BType()), FuncType([UType(), SType()], BType())]
            case "LIKE":
                return [FuncType([SType(), SType()], BType())]
            case "+":
                # SType candidate covers MSSQL's string concatenation via +.
                # BType candidate matches the engine-side rewrite that wraps
                # bool predicates as CASE WHEN ... THEN 1 ELSE 0 END.
                # (Z,U)/(U,Z)/(R,U)/(U,R)/(S,U)/(U,S) candidates break the
                # cost tie when a NULL literal meets a typed operand.
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], RType()),
                        FuncType([SType(), SType()], SType()), FuncType([UType(), UType()], UType()),
                        FuncType([BType(), ZType()], ZType()), FuncType([ZType(), BType()], ZType()),
                        FuncType([BType(), BType()], ZType()),
                        FuncType([ZType(), UType()], ZType()), FuncType([UType(), ZType()], ZType()),
                        FuncType([RType(), UType()], RType()), FuncType([UType(), RType()], RType()),
                        FuncType([SType(), UType()], SType()), FuncType([UType(), SType()], SType())]
            case "-" | "*" | "/":
                # Arithmetic — no string overload here.
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], RType()),
                        FuncType([UType(), UType()], UType()),
                        FuncType([BType(), ZType()], ZType()), FuncType([ZType(), BType()], ZType()),
                        FuncType([BType(), BType()], ZType()),
                        FuncType([ZType(), UType()], ZType()), FuncType([UType(), ZType()], ZType()),
                        FuncType([RType(), UType()], RType()), FuncType([UType(), RType()], RType())]
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
            case (ZType(), RType()) | (SType(), ZType()) | (SType(), RType()) | (SType(), DTType()) | (UType(), _):
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
        match e:
            case BValue() | Natural() | Real() | SString() | Boolean():
                self.cast(e, t)
                return True
            case _:
                return True
        return False

    def cast(self, e: Expression, t: ValueType):
        """
        This function represents an explicit cast in the paper. It is used to cast a value to a specific type.
        """
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match (e, t):
            case (Nullv(), _):
                return e
            case(Real(), RType()):
                v = Real(Decimal(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (v, t) if self.ty(v) == t:
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), RType()):
                v = Real(float(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Boolean(), ZType()):
                v = Natural(1 if e.v else 0)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), ZType()):
                v = Natural(int(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), SType()) | (Real(), SType()) | (Boolean(), SType()):
                v = SString(str(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), ZType()):
                try:
                    if e.v == '':
                        v = Natural(0)
                        v.unknown = t.tag == 'Unknown'
                        return v
                    n = int(e.v)
                    v = Natural(n)
                    v.unknown = t.tag == 'Unknown'
                    return v
                except:
                    raise Exception(f"cast fails {e} to {t}")
            case(SString(), RType()):
                try:
                    r = float(e.v)
                    v = Real(r)
                    v.unknown = t.tag == 'Unknown'
                    return v
                except:
                    raise Exception(f"cast fails {e} to {t}")
            case (SString(), BType()) if e.v.lower() == 'true' or e.v.lower() == 'false':
                v = Boolean(e.v.lower() == 'true')
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), BType()) if e.v in (0, 1):
                v = Boolean(bool(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (DateTime(), DTType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (DateTime(), SType()):
                dt = e.v
                if hasattr(dt, "strftime"):
                    # SQL Server formats DATE-like values differently from DATETIME-like
                    # values when implicitly converted for string comparisons.
                    if getattr(dt, "hour", 0) == 0 and getattr(dt, "minute", 0) == 0 and getattr(dt, "second", 0) == 0 and getattr(dt, "microsecond", 0) == 0:
                        s = dt.strftime("%Y-%m-%d")
                    else:
                        s = dt.strftime("%b %d %Y %I:%M%p")
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
        if v1.erase() == None or v2.erase() == None:
            return BValue(None)
        match op:
            case "<":
                return BValue(v1.erase() < v2.erase())
            case "=":
                return BValue(v1.erase() == v2.erase())
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
                result = re.match(pattern, str(v1.erase()), re.IGNORECASE | re.DOTALL) is not None
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

    def avg_value(self, total, count, elem_expr) -> BValue:
        # T-SQL truncates integer AVG toward zero; other numeric types keep decimals.
        elem_type = getattr(elem_expr, 't', None)
        if isinstance(elem_type, ZType):
            return Natural(int(total / count))
        return Real(total / count, use_decimal=True)


class Mssql(Engine):
    typechecker = Typechecker(MssqlOps())

    run = Runtime(MssqlOps())

    def __init__(self):
        self.tag = "Mssql"

    def __str__(self):
        return "Mssql"

    def infer_schema(self, connection):
        """Infer schema from MSSQL database using information_schema."""
        cursor = connection.cursor()
        schema = {}

        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_SCHEMA = 'dbo'
            ORDER BY TABLE_NAME
        """)

        tables = [row[0] for row in cursor.fetchall()]

        for table_name in tables:
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                AND TABLE_SCHEMA = 'dbo'
                ORDER BY ORDINAL_POSITION
            """, (table_name,))

            columns = cursor.fetchall()
            name_types = []

            for col_name, data_type in columns:
                interpreter_type = self._map_mssql_type(data_type)
                name_types.append(NameType(col_name, interpreter_type))

            schema[table_name.upper()] = RelationType(name_types)

        cursor.close()
        return schema

    def _map_mssql_type(self, data_type: str):
        """Map MSSQL data types to interpreter types."""
        data_type = data_type.lower()
        if data_type in ('int', 'bigint', 'smallint', 'tinyint'):
            return ZType()
        elif data_type in ('float', 'real', 'decimal', 'numeric', 'money', 'smallmoney'):
            return RType()
        elif data_type == 'bit':
            return BType()
        elif data_type in ('datetime', 'datetime2', 'smalldatetime', 'date', 'time', 'datetimeoffset'):
            return DTType()
        else:
            return SType()

    def comparev(self, v1, v2):
        # print("MSSQL comparev:", repr(v1), type(v1), repr(v2), type(v2))
        if isinstance(v2, Decimal) and type(v1) == float:
            if int(v1) == int(v2):
                return True
            else:
                return np.isclose(v1, float(v2))
        elif isinstance(v1, Decimal) and type(v2) == float:
            result = np.isclose(float(v1), float(v2))
            return result
        elif isinstance(v1, Decimal) and type(v2) == Decimal:
            result = np.isclose(float(v1), float(v2))
            return result
        elif isinstance(v1, Decimal) and isinstance(v2, Decimal):
            return np.isclose(float(v1), float(v2))
        elif type(v1) == float and type(v2) == float:
            return np.isclose(v1, v2)
        elif isinstance(v1, str) and isinstance(v2, str):
            return v1 == v2
        else:
            return v1 == v2
