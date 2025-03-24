from interpreter.syntax.expression.BExpr import *
from interpreter.syntax.Syntax import *

class Empty(BExpr):
    def __init__(self, q):
        self.q = q

    def __str__(self):
        return "Empty" + "(" + str(self.q) + ")"

    def __eq__(self, other):
        return self.q == other.q

    def run(self, db, row, attrnames, sql):
        t = self.q.run(db, sql)
        b = sql.doEmpty(t)
        return b
        # return BValue(0 if t == [] else 1)

    def typecheck(self, dbt, tablet, sql):
        t = self.q.typecheck(dbt, sql)
        return sql.resTypeEq()

    def trans(self, dbt, tablet, sql):
        q = self.q.trans(dbt, sql)
        return Empty(q)

