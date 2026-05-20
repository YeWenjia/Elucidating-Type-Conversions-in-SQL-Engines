from .Engine import Engine
import math
import re
from decimal import Decimal
import numpy as np
from interpreter import Runtime
from interpreter.syntax.expression.Op import *
from interpreter.Typechecker import *
from interpreter.Runtime import *
from interpreter.AbstractOps import *
import re
import builtins



class MysqlOps(AbstractOps):
    use_truth_value_for_logical_ops = True
    _REAL_PREFIX_RE = re.compile(r'^\s*[-+]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][-+]?[0-9]+)?')
    _INT_PREFIX_RE = re.compile(r'^\s*[-+]?[0-9]+')

    def truth_value(self, v):
        value = v.erase()
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, Decimal)):
            return value != 0
        if isinstance(value, str):
            match = re.match(r'^[-+]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][-+]?[0-9]+)?', value.strip())
            if not match:
                return False
            try:
                return float(match.group()) != 0.0
            except ValueError:
                return False
        return bool(value)

    def check_boolean(self, t, e=None):
        return ZType()

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

    def normalize_for_comparison(self, value):
        if isinstance(value, str):
            return value.lower()
        return value

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        if op in ("<", "="):
            match (t1, t2):
                case (SType(), BType()):
                    return FuncType([RType(), RType()], ZType())
                case (BType(), SType()):
                    return FuncType([RType(), RType()], ZType())
        t3s = self.ty_op(op)
        return self.best_candidate(t1, t2, t3s)
    
    def resolve_agg_func(self, e, t, agg_func):
        match agg_func:
            case "COUNT":
                return FuncType(t, NumType())
            case "SUM":
                return FuncType(NumType(), NumType())
            case "AVG":
                return FuncType(NumType(), NumType())
            case "MAX" | "MIN":
                return FuncType([t], t)
            case _:
                raise Exception(f"Unknown aggregate function: {agg_func}")

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], ZType()), FuncType([SType(), SType()], ZType()), FuncType([UType(), UType()], ZType()), FuncType([DTType(), DTType()], ZType()), FuncType([BType(), BType()], ZType())]
            case "=":
                return [FuncType([ZType(), ZType()], ZType()),FuncType([RType(), RType()], ZType()), FuncType([SType(), SType()], ZType()), FuncType([UType(), UType()], ZType()), FuncType([DTType(), DTType()], ZType()), FuncType([BType(), BType()], ZType())]
            case "LIKE":
                return [FuncType([SType(), SType()], ZType())]
            case "+" | "-" | "*" | "/":
                return [FuncType([NumType(), NumType()], NumType())]
            case _:
                raise Exception(f"Operation not found: {op}")

    def best_candidate(self, t1, t2, t3s):
        ms = list(map(lambda x: (self.cost(t1, x.dom[0]) + self.cost(t2, x.dom[1])), t3s))
        min_val = min(ms)
        if ms.count(min_val) == 1:
            argmin = ms.index(min_val)
            candidate = t3s[argmin]
            return candidate
        else:
            raise TypeError(f"No best candidate for the given types {t1}, {t2}. Options are: {[(t3.__str__(), self.cost(t1, t3.dom[0]) + self.cost(t2, t3.dom[1])) for t3 in t3s]}")

    def cost(self, t1, t2) -> int:
        match (t1, t2):
            case (t1, t2) if t1 == t2:
                return 0
            case (ZType(), ZType()):
                return 0
            case (ZType(), RType()):
                return 0.5
            case (SType(), RType()):
                return 1
            case (SType(), DTType()):
                return 1
            case (NumType(), RType()):
                return 0
            case (UType(), _):
                return 1
            case _:
                return 2

    def biconv(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType):
        return self.uicast(t1, t2)

    def uicast(self, t1, t2):
        match (t1, t2):
            case (t1, t2) if t1 == t2:
                return t1
            case (SType(), t2):
                return SType()
            case (t1, SType()):
                return SType()
            case (RType(), t2) if t2 != SType():
                return RType()
            case (t1, RType()) if t1 != SType():
                return RType()
            case (NumType(), ZType())| (ZType(), NumType()) :
                return RType()
            case ((UType(), t2)| (t2, UType())):
                return UType()
            case _:
                raise TypeError(f"biconv fails {t1} to {t2}")


    def explicit_cast_feasibility(self, e: Expression, tp: ValueType, t: ValueType):
        return True

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
            case (Real(), RType()):
                v = Real(Decimal(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (v, t) if self.ty(v) == t:
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), SType()) | (Real(), SType()) | (Boolean(), SType()):
                v = SString(str(e.v))
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
            case (Natural(), RType()):
                v = Real(float(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), ZType()):
                match = self._INT_PREFIX_RE.match(e.v)
                if match:
                    text = match.group().strip()
                    if '.' in text:
                        number = float(text)
                        v = Natural(int(number))
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        v = Natural(int(text))
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), RType()):
                match = self._REAL_PREFIX_RE.match(e.v)
                if match:
                    number = float(match.group().strip())
                    if math.isfinite(number) and number == int(number):
                        v = Real(float(number))
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        v = Real(number)
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Real(0.0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), NumType()):
                match = self._REAL_PREFIX_RE.match(e.v)
                if match:
                    text = match.group().strip()
                    if '.' in text or 'e' in text.lower():
                        number = float(text)
                        v = Real(number)
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        v = Natural(int(text))
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), BType()):
                match = self._REAL_PREFIX_RE.match(e.v)
                if match:
                    number = float(match.group().strip())
                    if math.isfinite(number) and number == int(number):
                        v = Natural(int(number))
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        v = Real(number)
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (Natural(), NumType()) | (Real(), NumType()):
                return e
            case (DateTime(), DTType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (DateTime(), SType()):
                v = SString(str(e.v))
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
            case (e, UType()):
                return e
        raise TypeError(f"cast fails {e} to {t}")

    def insert(self, e: Expression, t: ValueType, op: str) -> Expression:
        return Ascr(e, t)

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
        if v1.erase() == None or v2.erase() == None:
            return BValue(None)
        match op:
            case "<":
                match (type(v1.erase()), type(v2.erase())):
                    case (builtins.str, builtins.str):
                        return BValue(1 if v1.erase().lower() < v2.erase().lower() else 0)
                    case _:
                        return BValue(1 if v1.erase() < v2.erase() else 0)
            case "=":
                if isinstance(v1.erase(), str) and isinstance(v2.erase(), str):
                    return BValue(1 if v1.erase().lower() == v2.erase().lower() else 0)
                return BValue(1 if v1.erase() == v2.erase() else 0)
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
                # Match the entire string (case-sensitive for MySQL with utf8mb4_bin collation)
                pattern = '^' + pattern + '$'
                result = re.match(pattern, str(v1.erase()), re.IGNORECASE | re.DOTALL) is not None
                return BValue(1 if result else 0)
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

    def clean(self, T: RelationType) -> RelationType:
        return T

    def resTypeE(self):
        return RType()

    def doEmpty(self, t):
        return BValue(0 if t.rows == [] else 1)

    def doIn(self, es, rs):
        has_null = False

        for r in rs:
            all_true = True
            has_false = False

            for i, e in enumerate(es):
                rr = r[i]
                bb = self.apply("=", e, rr)
                result = changeb(bb)

                if result == False:
                    has_false = True
                    all_true = False
                    break
                elif result is None:
                    all_true = False

            if all_true:
                return BValue(True)
            elif not has_false:
                has_null = True

        return BValue(None) if has_null else BValue(False)

    def isnull_res(self, v):
        return BValue(1 if v.v is None else 0)

    def restype_E(self):
        return ZType()

    def boolean_value(self, v):
        return BValue(1 if v else 0)




class Mysql(Engine):
    typechecker = Typechecker(MysqlOps())

    run = Runtime(MysqlOps())

    def __init__(self):
        self.tag = "Mysql"

    def __str__(self):
        return "Mysql"

    def comparev(self, v1, v2):
        if (type(v1) == bool):
            if v1 == True:
                if v2 == 1:
                    return True
                else:
                    return False
            elif v1 == False:
                if v2 == 0:
                    return True
                else:
                    return False
        elif isinstance(v2, Decimal) and type(v1) == float:
            v2 = float(v2)
            return np.isclose(v1, v2, atol=1e-4)
        elif isinstance(v1, Decimal) and type(v2) == float:
            v1 = float(v1)
            return np.isclose(v1, v2, atol=1e-4)
        elif isinstance(v1, Decimal) and isinstance(v2, Decimal):
            return np.isclose(float(v1), float(v2), atol=1e-4)
        else:
            try:
                f1 = float(v1)
                f2 = float(v2)
                return np.isclose(f1, f2, atol=1e-4)
            except:
                return v1 == v2

    def format(self, v):
        rv = super().format(v)
        if type(rv) == str:
            return rv.lower()
        else:
            return rv

    def infer_schema(self, connection):
        """Infer schema from MySQL database using information_schema."""
        cursor = connection.cursor()
        schema = {}

        # Get current database name
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (db_name,))

        tables = [row[0] for row in cursor.fetchall()]

        for table_name in tables:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
                ORDER BY ordinal_position
            """, (db_name, table_name))

            columns = cursor.fetchall()
            name_types = []

            for col_name, data_type in columns:
                interpreter_type = self._map_mysql_type(data_type)
                name_types.append(NameType(col_name, interpreter_type))

            schema[table_name.upper()] = RelationType(name_types)

        cursor.close()
        return schema

    def _map_mysql_type(self, data_type: str):
        """Map MySQL data types to interpreter types."""
        data_type = data_type.lower()
        if data_type in ('int', 'integer', 'bigint', 'smallint', 'tinyint', 'mediumint'):
            return ZType()
        elif data_type in ('float', 'double', 'decimal', 'numeric', 'real'):
            return RType()
        elif data_type in ('tinyint(1)', 'boolean', 'bool'):
            return BType()
        elif data_type in ('datetime', 'timestamp', 'date', 'time'):
            return DTType()
        else:
            return SType()
