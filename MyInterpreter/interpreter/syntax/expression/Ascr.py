from interpreter.syntax.expression.Expression import Expr


class Ascr(Expr):
    def __init__(self, e, t):
        self.t = t
        self.e = e

    def __str__(self):
        return "(" + str(self.e) + " :: " + str(self.t) + ")"

    def __eq__(self, other):
        return self.e == other.e and self.t == other.t

    # def run(self, db, row, attrnames, sql):
    #     e = self.e.run(db, row, attrnames, sql)
    #     return e.cast(self.t, sql)
    #
    # def typecheck(self, dbt, tablet, sql):
    #     t0 = self.e.typecheck(dbt, tablet, sql)
    #     if sql.ExCast(self.e, t0, self.t):
    #         return self.t
    #     else:
    #         raise Exception("Program does not type check")
    #
    # def trans(self, dbt, tablet, sql):
    #     ee = self.e.trans(dbt, tablet, sql)
    #     return Ascr(ee, self.t)
