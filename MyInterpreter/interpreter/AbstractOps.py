from interpreter.syntax.expression import Expression
from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.expression.Op import Op
from interpreter.syntax.type.ValueType import ValueType, FuncType, ZType, RType
from interpreter.syntax.type.ValueType import *
from interpreter.syntax.type.RelationType import *

class AbstractOps:
    def ty(self, v: Expression) -> ValueType:
        raise Exception(f"'ty' function not implemented")

    def resolve(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType, op: Op) -> FuncType:
        raise Exception(f"'resolve' function not implemented")

    def biconv(self, e1: Expression, t1: ValueType, e2: Expression, t2: ValueType):
        raise Exception(f"'biconv' function not implemented")

    def insert(self, e: Expression, t: ValueType, op: str) -> Expression:
        """
        This function corresponds to the insert operator of the paper, and it is used to insert casts on the type of the
        result of a set operation
        """
        raise Exception(f"'Insert' function not implemented")

    def cast(self, e: Expression, t: ValueType) -> BValue:
        """
        This function corresponds to the explicit cast
        """
        raise Exception(f"'Cast' function not implemented")

    def explicit_cast_feasibility(self, e: Expression, tp: ValueType, t: ValueType):
        """
        This function corresponds to the explicit cast feasibility operator e:τ'⇝τ
        """
        raise Exception(f"'ExplicitCast' function not implemented")

    def type_implicit_cast(self, t1, t2):
        match (t1, t2):
            case (t1, t2) if t1 == t2:
                return True
            case (ZType(), RType()):
                return True
            case _:
                return False

    def clean(self, T: RelationType) -> RelationType:
        return T

    def check_boolean(self, t):
        return t

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
        raise Exception(f"'apply' function not implemented")
