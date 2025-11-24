from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.type.ValueType import BType, ZType
from interpreter.syntax.expression.BExpr import *

class Or(BExpr):
    def __init__(self, l, r):
        super().__init__()
        self.l = l
        self.r = r
        self.isnull_not_null = False

    def __str__(self):
        return "(" + str(self.l) + " ∨ " + str(self.r) + ")"

    def __eq__(self, other):
        return self.l == other.l and self.r == other.r

    