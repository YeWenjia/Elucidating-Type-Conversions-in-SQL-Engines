from interpreter.syntax.expression.BValue import BValue, Nullv
from interpreter.syntax.type.ValueType import BType, ZType
from interpreter.syntax.expression.BExpr import *

class IsNull(BExpr):
    def __init__(self, e):
        super().__init__()
        self.e = e
        if isinstance(self.e, Nullv) or self.e.isnull:
            self.isnull_not_null = False
        else:
            self.isnull_not_null = True

    def __str__(self):
        return str(self.e) + " IS NULL"

    def __eq__(self, other):
        return self.e == other.e