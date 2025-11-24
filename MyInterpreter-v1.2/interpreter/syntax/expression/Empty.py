from interpreter.syntax.expression.BExpr import *
from interpreter.syntax.Syntax import *

class Empty(BExpr):
    def __init__(self, q):
        super().__init__()
        self.q = q

    def __str__(self):
        return "Empty" + "(" + str(self.q) + ")"

    def __eq__(self, other):
        return self.q == other.q

