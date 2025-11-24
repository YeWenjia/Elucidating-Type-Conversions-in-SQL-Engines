from .Engine import Engine
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
            case _:
                raise TypeError(f"Type not found: {e}")

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        t3s = self.ty_op(op)
        return self.best_candidate(t1, t2, t3s)

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                return [FuncType([RType(), RType()], RType()), FuncType([SType(), SType()], RType()), FuncType([UType(), UType()], RType())]
            case "=":
                return [FuncType([RType(), RType()], RType()), FuncType([SType(), SType()], RType()), FuncType([UType(), UType()], RType())]
            case "+":
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
            raise TypeError(f"No best candidate for the given types {t1}, {t2}")

    def cost(self, t1, t2) -> int:
        match (t1, t2):
            case (t1, t2) if t1 == t2:
                return 0
            case (ZType(), RType()):
                return 0
            case (SType(), RType()):
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
                match = re.match(r'^[-+]?\d+', e.v)
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
                match = re.match(r'^[-+]?(\d+(\.\d+)?|\.\d+)', e.v)
                if match:
                    number = float(match.group())
                    if number == int(number):
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
                match = re.match(r'^[-+]?(\d+(\.\d+)?|\.\d+)', e.v)
                if match:
                    if '.' in match.group():
                        number = float(match.group())
                        v = Real(number)
                        v.unknown = t.tag == 'Unknown'
                        return v
                    else:
                        v = Natural(v)
                        int(match.group())
                        return v
                else:
                    v = Natural(0)
                    v.unknown = t.tag == 'Unknown'
                    return v
            case (SString(), BType()):
                match = re.match(r'\d+(\.\d+)?', v)
                if match:
                    number = float(match.group())
                    if number == int(number):
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
                match (type(v1.erase()), type(v2.erase())):
                    case (builtins.str, builtins.str):
                        return BValue(1 if v1.erase().lower() == v2.erase().lower() else 0)
                    case _:
                        return BValue(1 if v1.erase() == v2.erase() else 0)
            case "+":
                r = v1.erase() + v2.erase()
                return BValue(r)
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
            return np.isclose(v1, v2)
        else:
            try:
                f1 = float(v1)
                f2 = float(v2)
                return np.isclose(f1, f2)
            except:
                return v1 == v2

    def format(self, v):
        rv = super().format(v)
        if type(rv) == str:
            return rv.lower()
        else:
            return rv


