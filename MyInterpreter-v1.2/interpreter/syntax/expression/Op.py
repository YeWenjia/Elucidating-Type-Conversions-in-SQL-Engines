from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.BValue import BValue
# from interpreter.syntax.expression.Expression import get_cop
from interpreter.syntax.type.ValueType import ZType, UType, BType
from interpreter.syntax.expression.BExpr import *


class Op(BExpr):
    def __init__(self, op, e1, e2):
        self.op = op
        self.e1 = e1
        self.e2 = e2
        self.isnull = self.e1.isnull or self.e2.isnull
        self.isnull_not_null = False

    def __str__(self):
        return "(" + str(self.e1) + " " + str(self.op) + " " + str(self.e2) + ")"

    def __eq__(self, other):
        return self.op == other.op and self.e1 == other.e1 and self.e2 == other.e2


class Oc(Op):
    pass


class Lt(Oc):
    def __init__(self, e1, e2):
        super(Lt, self).__init__("<", e1, e2)


class Eq(Oc):
    def __init__(self, e1, e2):
        super(Eq, self).__init__("=", e1, e2)


class Oa(Op):
    pass


class Plus(Oa):
    def __init__(self, e1, e2):
        super(Plus, self).__init__("+", e1, e2)

