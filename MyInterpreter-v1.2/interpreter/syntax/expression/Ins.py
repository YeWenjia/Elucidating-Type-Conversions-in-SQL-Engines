from interpreter.syntax.expression.BExpr import *
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression.Op import *
from interpreter.syntax.expression.NName import *

freshindex = 0

class Ins(BExpr):
    def __init__(self, es, q):
        super().__init__()
        self.es = es
        self.q = q

    def __str__(self):
        return "(" + str(self.es) + " in " + str(self.q) + ")"

    def __eq__(self, other):
        return self.q == other.q and self.es == other.es


