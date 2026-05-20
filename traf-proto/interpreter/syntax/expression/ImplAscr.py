from interpreter.syntax.expression.Expression import Expr


class ImplAscr(Expr):
    def __init__(self, e, t):
        self.t = t
        self.e = e
        self.isnull = self.e.isnull

    def __str__(self):
        return "(" + str(self.e) + " => " + str(self.t) + ")"

    def __eq__(self, other):
        return self.e == other.e and self.t == other.t

    # def run(self, db, row, attrnames, sql):
    #     e = self.e.run(db, row, attrnames, sql)
    #     return sql.icast(e, self.t)
    #
    # def typecheck(self, dbt, tablet, sql):
    #     t0 = self.e.typecheck(dbt, tablet, sql)
    #     if sql.UImCast(self.e, t0, self.t):
    #         return self.t
    #     else:
    #         raise Exception("Program does not type check")
    #

