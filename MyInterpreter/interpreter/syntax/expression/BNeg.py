from interpreter.syntax.expression.BValue import *
from interpreter.syntax.expression.BExpr import *
from interpreter.syntax.type.ValueType import BType, ZType


class BNeg(BExpr):
    def __init__(self, b):
        self.b = b

    def __str__(self):
        return "¬(" + str(self.b) + ")"

    def __eq__(self, other):
        return self.b == other.b

    # def run(self, db, row, attrnames, sql):
    #     b = self.b.run(db, row, attrnames, sql)
    #     if b.erase() == 1:
    #         return Natural(0)
    #     elif b.erase() == 0:
    #         return Natural(1)
    #     else:
    #         return Boolean(not b.erase())
    #
    # def typecheck(self, dbt, tablet, sql):
    #     b = self.b.typecheck(dbt, tablet, sql)
    #     if b.tag == "Bool":
    #         return BType()
    #     elif sql.tag in ["Sqlite","Mysql"]:
    #         return ZType()
    #     else:
    #         raise Exception("Program does not type check")
    #
    # def trans(self, dbt, tablet, sql):
    #     bb = self.b.trans(dbt, tablet, sql)
    #     return BNeg(bb)
