from interpreter.syntax.expression.BValue import BValue
from interpreter.syntax.type.ValueType import BType, ZType
from interpreter.syntax.expression.BExpr import *

class Or(BExpr):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __str__(self):
        return "(" + str(self.l) + " ∨ " + str(self.r) + ")"

    def __eq__(self, other):
        return self.l == other.l and self.r == other.r

    def run(self, db, row, attrnames, sql):
        # l = self.l.run(db, row, attrnames, sql)
        # if (l.erase() == 1):
        #     return l
        # elif (l.erase() == True):
        #     return l
        # r = self.r.run(db, row, attrnames, sql)
        l = self.l.run(db, row, attrnames, sql)
        r = self.r.run(db, row, attrnames, sql)
        if (l.erase() == 1):
            return l
        elif (l.erase() == True):
            return l
        return r


    def typecheck(self, dbt, tablet, sql):
        t1 = self.l.typecheck(dbt, tablet, sql)
        t2 = self.r.typecheck(dbt, tablet, sql)
        if t1.tag == t2.tag == "Bool":
            return BType()
        elif sql.tag in ["Mysql"]:
            return RType()
        elif sql.tag in ["Sqlite"]:
            return UType()
        else:
            raise Exception("Program does not type check")

    def trans(self, dbt, tablet, sql):
        ll = self.l.trans(dbt, tablet, sql)
        rr = self.r.trans(dbt, tablet, sql)
        return Or(ll, rr)
