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
            case _:
                raise TypeError(f"Type not found: {e}")

    def uicast(self, e, t1, t2):
        match t1:
            case SType():
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

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType())]
            case "=":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType())]
            case "+":
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], RType()),
                        FuncType([SType(), SType()], SType())]
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
            case (ZType(), RType()) | (SType(), ZType()) | (SType(), RType()):
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
        raise TypeError(f"cast fails {e} to {t}")

    def insert(self, e: Expression, t: ValueType, op: str) -> Expression:
        return Ascr(e, t)

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
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

class Mssql(Engine):
    typechecker = Typechecker(MssqlOps())

    run = Runtime(MssqlOps())

    def __init__(self):
        self.tag = "Mssql"

    def __str__(self):
        return "Mssql"

    def comparev(self, v1, v2):
        # if isinstance(v2, Decimal) and type(v1) == float:
        #     return np.isclose(v1, float(v2))
        if isinstance(v2, Decimal) and type(v1) == float:
            if int(v1) == int(v2):
                return True
            else:
                return np.isclose(v1, float(v2))

        else:
            return v1 == v2





