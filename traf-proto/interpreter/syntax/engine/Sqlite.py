from .Engine import Engine
import re
import datetime
from decimal import Decimal
import numpy as np
from interpreter import Runtime
from interpreter.syntax.expression.Op import *
from interpreter.Typechecker import *
from interpreter.Runtime import *
from interpreter.AbstractOps import *
import re


class SqliteOps(AbstractOps):
    use_truth_value_for_logical_ops = True

    def truth_value(self, v):
        value = v.erase()
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            text = value.strip()
            match = re.match(r'^[-+]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][-+]?[0-9]+)?', text)
            if not match:
                return False
            try:
                return float(match.group()) != 0.0
            except ValueError:
                return False
        if isinstance(value, (int, float, Decimal)):
            return value != 0
        return bool(value)

    def ty(self, e: Expression):
        return UType()

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        if op == "<":
            match (t1, t2):
                case (BType(), BType()):
                    return FuncType([BType(), BType()], UType())
        if op == "=":
            match (t1, t2):
                case (BType(), ZType()):
                    return FuncType([BType(), ZType()], UType())
                case (ZType(), BType()):
                    return FuncType([ZType(), BType()], UType())
                case (BType(), SType()):
                    return FuncType([BType(), SType()], UType())
                case (SType(), BType()):
                    return FuncType([SType(), BType()], UType())
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
                return [FuncType([RType(), RType()], UType()), FuncType([SType(), SType()], UType()),
                        FuncType([UType(), UType()], UType()), FuncType([DTType(), DTType()], UType())]
            case "=":
                return [FuncType([RType(), RType()], UType()), FuncType([SType(), SType()], UType()),
                        FuncType([UType(), UType()], UType()), FuncType([DTType(), DTType()], UType()),
                        FuncType([BType(), BType()], UType())]
            case "LIKE":
                return [FuncType([SType(), SType()], UType())]
            case "+" | "-" | "*" | "/":
                return [FuncType([NumType(), NumType()], UType())]
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
            case (SType(), RType()):
                return 1
            case (UType(), t2):
                return 1
            case _:
                return 2

    def biconv(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType):
        return UType()

    def explicit_cast_feasibility(self, e: Expression, tp: ValueType, t: ValueType):
        return True

    def icast(self, e, t):
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match (e, t):
            case (Nullv(), _):
                e.unknown = t.tag == 'Unknown'
                return e
            case (Natural(), RType()):
                v = Real(float(e.v), False)
                v.unknown = t.tag == 'Unknown'
                return v
            case (v, t) if self.typeof(v) == t:
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), SType()) | (Real(), SType()) | (Boolean(), SType()):
                v = SString(str(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), ZType()):
                v = Natural(int(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), RType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (Boolean(), ZType()):
                v = Natural(1 if e.v else 0)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Boolean(), RType()):
                v = Real(1.0 if e.v else 0.0, False)
                v.unknown = t.tag == 'Unknown'
                return v
            case (Boolean(), NumType()):
                v = Natural(1 if e.v else 0)
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), ZType()):
                try:
                    v = Natural(int(e.v))
                    v.unknown = t.tag == 'Unknown'
                    return v
                except:
                    e.unknown = t.tag == 'Unknown'
                    return e
            case (SString(), RType()):
                try:
                    v = Real(float(e.v), False)
                    v.unknown = t.tag == 'Unknown'
                    return v
                except:
                    e.unknown = t.tag == 'Unknown'
                    return e
            case (SString(), NumType()):
                match = re.match(r'^[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)', e.v)
                if match:
                    if '.' in match.group():
                        number = float(match.group())
                        v = Real(number, False)
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        number =int(match.group())
                        v = Natural(number, False)
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), BType()):
                try:
                    v = Natural(int(e.v))
                    v.unknown = t.tag == 'Unknown'
                    return v
                except:
                    e.unknown = t.tag == 'Unknown'
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
            case (DateTime(), UType()):
                e.unknown = True
                return e
            case (v, UType()):
                v.unknown = True
                return v
        raise TypeError(f"cast fails {e} to {t}")

    def cast(self, e: Expression, t: ValueType):
        """
        This function represents an explicit cast in the paper. It is used to cast a value to a specific type.
        """
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match (e, t):
            case (Nullv(), _):
                e.unknown = t.tag == 'Unknown'
                return e
            case (Real(), RType()):
                # v = Real(Decimal(e.v))
                v = Real(e.v, False)
                v.unknown = t.tag == 'Unknown'
                return v
            case (v, t) if self.typeof(v) == t:
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), SType()) | (Real(), SType()) | (Boolean(), SType()):
                v = SString(str(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), ZType()):
                v = Natural(int(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), RType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (SString(), ZType()):
                match = re.match(r'^[-+]?[0-9]+', e.v)
                if match:
                    if '.' in match.group():
                        number = float(match.group())
                        v = Natural(int(number))
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        v = Natural(int(match.group()))
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), RType()):
                match = re.match(r'^[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)', e.v)
                if match:
                    number = float(match.group())
                    v = Real(number, False)
                    v.unknown = t.tag == 'Unknown'
                    return v
                else:
                    v = Real(0, False)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), NumType()):
                match = re.match(r'^[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)', e.v)
                if match:
                    if '.' in match.group():
                        number = float(match.group())
                        v = Real(number, False)
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        number = int(match.group())
                        v = Natural(number, False)
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), BType()):
                match = re.match(r'[0-9]+(\.[0-9]+)?', e.v)
                if match:
                    number = float(match.group())
                    if number == int(number):
                        v = Natural(int(number))
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        v = Real(number, False)
                        v.unknown = t.tag == 'Unknown'
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (v, UType()):
                v.unknown = True
                return v
            case (Natural(), NumType()) | (Real(), NumType()):
                e.unknown = t.tag == 'Unknown'
                return e
        raise TypeError(f"cast fails {e} to {t}")

    def insert(self, e: Expression, t: ValueType, op: str) -> Expression:
        match op:
            case "<":
                return e
            case "=":
                return e
            case "+":
                return Ascr(e, t)
            case _:
                return Ascr(e, t)

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
        if v1.v is None or v2.v is None:
            return BValue(None, False)
        match op:
            case "<":
                cpVal = lambda x, y: x < y
                cpTy = lambda x, y: (x == int or x == float or x == Decimal) and (y == str)
                r = self.doCp(v1, v2, op, cpVal, cpTy)
                return r
            case "=":
                cpVal = lambda x, y: x == y
                cpTy = lambda x, y: False
                r = self.doCp(v1, v2, op, cpVal, cpTy)
                return r
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
                # Match the entire string (case-insensitive for SQLite)
                pattern = '^' + pattern + '$'
                result = re.match(pattern, str(v1.erase()), re.IGNORECASE | re.DOTALL) is not None
                return Natural(1 if result else 0)
            case "+":
                r = v1.erase() + v2.erase()
                # print("ble", [v1.v, v2.v])
                return BValue(r, False)
            case "-":
                return BValue(v1.erase() - v2.erase(), False)
            case "*":
                return BValue(v1.erase() * v2.erase(), False)
            case "/":
                return BValue(v1.erase() / v2.erase(), False)
            case _:
                raise TypeError(f"operation {op} not support")

    def typeof(self, v):
        if type(v.v) == int:
            return ZType()
        elif type(v.v) == float:
            return RType()
        elif type(v.v) == str:
            return SType()
        elif type(v.v) == Decimal:
            return RType()
        elif type(v.v) == bool:
            return BType()
        elif isinstance(v.v, (datetime.datetime, datetime.date, datetime.time)):
            return DTType()

    def doCp(self, v1, v2, op, cpVal, cpTy):
        # print(f"comparing {v1} and {v2}")
        if v1.unknown:
            ty1 = UType()
            if v2.unknown:
                ty2 = UType()
            else:
                ty2 = self.typeof(v2)
        else:
            ty1 = self.typeof(v1)
            if v2.unknown:
                ty2 = UType()
            else:
                ty2 = self.typeof(v2)
        tt = self.resolve(v1, ty1, v2, ty2, op)
        v1 = self.icast(v1, tt.dom[0])
        v2 = self.icast(v2, tt.dom[1])
        val1 = int(v1.erase()) if isinstance(v1.erase(), bool) else v1.erase()
        val2 = int(v2.erase()) if isinstance(v2.erase(), bool) else v2.erase()
        ty1 = type(val1)
        ty2 = type(val2)
        if ty1 == ty2:
            if cpVal(val1, val2):
                return Natural(1)
            else:
                return Natural(0)
        elif ty1 in [int, float, Decimal] and ty2 in [int, float, Decimal]:
            if cpVal(val1, val2):
                return Natural(1)
            else:
                return Natural(0)
        elif cpTy(ty1, ty2):
            return Natural(1)
        else:
            return Natural(0)

    def resTypeE(self):
        return UType()

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

    def boolean_value(self, v):
        return BValue(1 if v else 0)




class Sqlite(Engine):
    typechecker = Typechecker(SqliteOps())

    run = Runtime(SqliteOps())

    def __init__(self):
        self.tag = "Sqlite"

    def __str__(self):
        return "Sqlite"

    def _datetime_for_compare(self, value):
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if isinstance(value, str):
            try:
                return datetime.datetime.fromisoformat(value.strip())
            except ValueError:
                return None
        return None

    def typeof(self, v):
        if type(v.v) == int:
            return ZType()
        elif type(v.v) == float:
            return RType()
        elif type(v.v) == str:
            return SType()
        elif type(v.v) == Decimal:
            return RType()
        elif isinstance(v.v, (datetime.datetime, datetime.date, datetime.time)):
            return DTType()

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
        elif (
            isinstance(v1, (datetime.datetime, datetime.date))
            or isinstance(v2, (datetime.datetime, datetime.date))
        ):
            dt1 = self._datetime_for_compare(v1)
            dt2 = self._datetime_for_compare(v2)
            return dt1 is not None and dt2 is not None and dt1 == dt2
        elif isinstance(v2, Decimal) and type(v1) == float:
            v2 = float(v2)
            return np.isclose(v1, v2)
        elif isinstance(v1, Decimal) and type(v2) == float:
            v1 = float(v1)
            return np.isclose(v1, v2)
        elif isinstance(v1, Decimal) and isinstance(v2, Decimal):
            v1 = float(v1)
            v2 = float(v2)
            return np.isclose(v1, v2)
        elif type(v1) == type(v2) == str:
            try:
                tv1 = float(v1)
                tv2 = float(v2)
                return tv1 == tv2
            except ValueError:
                return v1 == v2
        else:
            return v1 == v2

    def infer_schema(self, connection):
        """Infer schema from SQLite database using sqlite_master and PRAGMA."""
        cursor = connection.cursor()
        schema = {}

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        for table_name in tables:
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns = cursor.fetchall()
            # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
            name_types = []

            for row in columns:
                col_name = row[1]
                data_type = (row[2] or '').upper()
                interpreter_type = self._map_sqlite_type(data_type)
                name_types.append(NameType(col_name, interpreter_type))

            schema[table_name.upper()] = RelationType(name_types)

        cursor.close()
        return schema

    def _map_sqlite_type(self, data_type: str):
        """Map SQLite data types to interpreter types."""
        data_type = data_type.upper().strip()
        if data_type in ('INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT', 'MEDIUMINT'):
            return ZType()
        elif data_type in ('REAL', 'FLOAT', 'DOUBLE', 'NUMERIC', 'DECIMAL'):
            return RType()
        elif data_type in ('BOOLEAN', 'BOOL'):
            return BType()
        elif data_type in ('DATETIME', 'TIMESTAMP', 'DATE', 'TIME'):
            return DTType()
        else:
            return SType()
