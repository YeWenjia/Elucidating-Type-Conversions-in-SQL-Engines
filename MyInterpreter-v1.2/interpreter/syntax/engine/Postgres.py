import numpy as np
from interpreter import Runtime
from interpreter.syntax.expression.Op import *
from interpreter.Typechecker import *
from interpreter.Runtime import *
from interpreter.AbstractOps import *
import re


class PostgresOps(AbstractOps):
    def clean(self, T: RelationType) -> RelationType:
        return RelationType(
            list(map(lambda x: NameType(x.name, SType()) if x.type.tag == "Unknown" else x, T.nametypes)))

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
                return UType()
            case Boolean():
                return BType()
            case Nullv():
                return UType()
            case _:
                raise TypeError(f"Type not found: {e}")

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        t3s = self.ty_op(op)
        match (t1, t2):
            case (UType(), UType()):
                t = self.best_candidate(SType(), SType(), t3s)
                return t
            case (UType(), _):
                t = self.best_candidate(t2, t2, t3s)
                self.icast(e1, t.dom[0])
                return t
            case (_, UType()):
                t = self.best_candidate(t1, t1, t3s)
                self.icast(e2, t.dom[1])
                return t
            case (_, _):
                return self.best_candidate(t1, t2, t3s)

    def ty_op(self, op: str) -> [FuncType]:
        match op:
            case "<":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType())]
            case "=":
                return [FuncType([ZType(), ZType()], BType()), FuncType([RType(), RType()], BType()),
                        FuncType([SType(), SType()], BType())]
            case "+":
                return [FuncType([ZType(), ZType()], ZType()), FuncType([RType(), RType()], RType())]
            case _:
                raise Exception(f"Operation not found: {op}")

    def best_candidate(self, t1, t2, t3s):
        ms = list(map(lambda x: self.cost(t1, x.dom[0]) + self.cost(t2, x.dom[1]), t3s))
        min_val = min(ms)
        if ms.count(min_val) == 1:
            argmin = ms.index(min_val)
            candidate = t3s[argmin]
            if self.type_implicit_cast(t1, candidate.dom[0]) and self.type_implicit_cast(t2, candidate.dom[1]):
                return candidate
            else:
                raise TypeError(f"Best candidate {candidate} does not match the types {t1}, {t2}")
        elif ms.count(min_val) > 1:
            raise TypeError(f"Ambiguous best candidate for the given types {t1}, {t2}")
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

    def icast(self, e, t):
        if isinstance(e, NName):
            return e
        b = e.unknown
        e = e.rawValueToObj()
        e.unknown = b
        match (e, t):
            case (Nullv(), _):
                return e
            case (Natural(), RType()):
                v = Real(float(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (Real(), RType()):
                v = Real(Decimal(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), SType()):
                e.unknown = t.tag == 'Unknown'
                return e
            case (v, t) if self.ty(v) == t:
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), ZType()) if re.match(r'^(-)?\d+$', e.v):
                v = Natural(int(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), RType()) if re.match(r'^(-)?(\d+(\.\d+)?)$', e.v):
                v = Real(Decimal(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
            case (SString(), BType()) if e.v.lower() == 'true' or e.v.lower() == 'false':
                v = Boolean(e.v.lower() == 'true')
                v.unknown = t.tag == 'Unknown'
                return v
            case (Natural(), SType()) | (Real(), SType()) | (Boolean(), SType()):
                v = SString(str(e.v))
                v.unknown = t.tag == 'Unknown'
                return v
        raise TypeError(f"icast fails {e} to {t}")

    def biconv(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType):
        if self.uicast(e1, t1, t2):
            return t2
        elif self.uicast(e2, t2, t1):
            return t1
        else:
            raise TypeError(f"biconv fails {e1}, {t1}, {e2}, {t2}")

    def uicast(self, e, t1, t2):
        match t1:
            case t1 if self.type_implicit_cast(t1, t2):
                return True
            case UType():
                self.icast(e, t2)
                return True
        return False

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
            case (v, t):
                return self.icast(v, t)
        raise TypeError(f"cast fails {e} to {t}")

    def insert(self, e: Expression, t: ValueType, op: str) -> Expression:
        return Ascr(e, t)

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
        if v1.v is None or v2.v is None:
            return BValue(None)
        else:
            match (op):
                case ("<"):
                    return BValue(v1.erase() < v2.erase())
                case ("="):
                    return BValue(v1.erase() == v2.erase())
                case ("+"):
                    r = v1.erase() + v2.erase()
                    return BValue(r)
                case _:
                    raise TypeError(f"operation {op} not support")


class Postgres(Engine):
    typechecker = Typechecker(PostgresOps())

    run = Runtime(PostgresOps())

    def __init__(self):
        self.tag = "Postgres"

    def __str__(self):
        return "Postgres"

    def comparev(self, v1, v2):
        if isinstance(v2, Decimal) and type(v1) == float:
            return np.isclose(v1, float(v2))
        elif isinstance(v1, Decimal) and type(v2) == float:
            return np.isclose(v2, float(v1))
        elif type(v2) == float and type(v1) == float:
            return np.isclose(v1, v2)
        else:
            return v1 == v2