from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.type.ValueType import BType, ZType
from interpreter.syntax.expression.BExpr import *

class IsNull(BExpr):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return str(self.e) + " IS NULL"

    def __eq__(self, other):
        return self.e == other.e