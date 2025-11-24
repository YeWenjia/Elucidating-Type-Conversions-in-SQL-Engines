import numpy as np
from interpreter import Runtime
from interpreter.syntax.expression.Op import *
from interpreter.Typechecker import *
from interpreter.Runtime import *
from interpreter.AbstractOps import *
import re

class OracleOps(AbstractOps):
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

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                return [FuncType([RType(), RType()], BType()), FuncType([SType(), SType()], BType()), FuncType([UType(), UType()], BType())]
            case "=":
                return [FuncType([RType(), RType()], BType()), FuncType([SType(), SType()], BType()), FuncType([UType(), UType()], BType())]
            case "+":
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
            case (SType(), RType()) | (UType(), _):
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
            case (SString(), RType()):
                try:
                    r = float(e.v)
                    v = Real(r)
                    v.unknown = t.tag == 'Unknown'
                    return v
                except:
                    raise Exception(f"cast fails {e} to {t}")
            case (SString(), BType()):
                if e.v == '1':
                    v = Boolean(True)
                    v.unknown = t.tag == 'Unknown'
                    return v
                elif e.v == '0':
                    v = Boolean(False)
                    v.unknown = t.tag == 'Unknown'
                    return v
                elif e.v.lower() == 'true':
                    v = Boolean(True)
                    v.unknown = t.tag == 'Unknown'
                    return v
                elif e.v.lower() == 'false':
                    v = Boolean(False)
                    v.unknown = t.tag == 'Unknown'
                    return v
                else:
                    TypeError(f"cast fails {e} to {t}")
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
            case "+":
                r = v1.erase() + v2.erase()
                return BValue(r)
            case _:
                raise TypeError(f"operation {op} not support")

    def check_optimization(self):
        return True

    def check_isnull_null(self):
        return True


class Oracle(Engine):
    typechecker = Typechecker(OracleOps())

    run = Runtime(OracleOps())

    def __init__(self):
        self.tag = "Oracle"

    def __str__(self):
        return "Oracle"

    def comparev(self, v1, v2):
        if isinstance(v2, Decimal) and type(v1) == float:
            v2 = float(v2)
            return np.isclose(v1, v2)
        elif isinstance(v1, Decimal) and type(v2) == float:
            v1 = float(v1)
            return np.isclose(v2, v1)
        elif type(v2) == float and type(v1) == float:
            return np.isclose(v1,v2)
        else:
            return v1 == v2


