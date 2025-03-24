from interpreter.syntax.engine.Engine import Engine
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.BValue import BValue
# from interpreter.syntax.expression.Expression import get_cop
from interpreter.syntax.type.ValueType import ZType, UType, BType
from interpreter.syntax.expression.BExpr import *


class Op(BExpr):
    def __init__(self, op, e1, e2):
        self.op = op
        self.e1 = e1
        self.e2 = e2

    def __str__(self):
        return "(" + str(self.e1) + " " + str(self.op) + " " + str(self.e2) + ")"

    def __eq__(self, other):
        return self.op == other.op and self.e1 == other.e1 and self.e2 == other.e2

    # def run(self, db, row, attrnames, sql: Engine):
    #     v1 = self.e1.run(db, row, attrnames, sql)
    #     v2 = self.e2.run(db, row, attrnames, sql)
    #     return self.doOperation(v1, v2, sql)
    #
    # def typecheck(self, dbt, tablet, sql):
    #     t1 = self.e1.typecheck(dbt, tablet, sql)
    #     t2 = self.e2.typecheck(dbt, tablet, sql)
    #     t = self.getCandidateTypes(sql)
    #     rt = sql.overload(self.e1, self.e2, t1, t2, t)
    #     return self.getResultType(sql, rt)
    #     # if sql.tag == 'Mysql':
    #     #     return ZType()
    #     # elif sql.tag == 'Sqlite':
    #     #     return UType()
    #     # else:
    #     #     return BType()
    #
    # def trans(self, dbt, tablet, sql):
    #     ee1 = self.e1.trans(dbt, tablet, sql)
    #     ee2 = self.e2.trans(dbt, tablet, sql)
    #     t1 = self.e1.typecheck(dbt, tablet, sql)
    #     t2 = self.e2.typecheck(dbt, tablet, sql)
    #     t = self.getCandidateTypes(sql)
    #     tt = sql.overload(self.e1, self.e2, t1, t2, t)
    #     return self.getTransResult(sql, ee1, ee2, tt)
    #     # if sql.tag == 'Sqlite':
    #     #     return Cp(self.op, ee1, ee2)
    #     # else:
    #     #     return Cp(self.op, Ascr(ee1, tt[0]), Ascr(ee2, tt[1]))
    #
    # def doOperation(self, v1, v2, sql: Engine):
    #     raise Exception("Operation " + str(self.op) + " not supported")
    #
    # # def doComparison(self, v1, v2, sql: Engine):
    # #     raise Exception("Operation " + str(self.op) + " not supported")


class Oc(Op):
    pass


class Lt(Oc):
    def __init__(self, e1, e2):
        super(Lt, self).__init__("<", e1, e2)

    # def getCandidateTypes(self, sql):
    #     return sql.getCandidateTypesLt()
    #
    # def doOperation(self, v1, v2, sql: Engine):
    #     return self.doComparison(v1, v2, sql)
    #
    # def doComparison(self, v1, v2, sql: Engine):
    #     return sql.doLt(v1, v2)
    #
    # def getResultType(self, sql, rt):
    #     return sql.resTypeLt()
    #
    # def getTransResult(self, sql, ee1, ee2, tt):
    #     return sql.transResLt(ee1, ee2, tt)


class Eq(Oc):
    def __init__(self, e1, e2):
        super(Eq, self).__init__("=", e1, e2)

    # def getCandidateTypes(self, sql):
    #     return sql.getCandidateTypesLt()
    #
    # def doOperation(self, v1, v2, sql: Engine):
    #     return self.doComparison(v1, v2, sql)
    #
    # def doComparison(self, v1, v2, sql: Engine):
    #     return sql.doEq(v1, v2)
    #
    # def getResultType(self, sql, rt):
    #     return sql.resTypeEq()
    #
    # def getTransResult(self, sql, ee1, ee2, tt):
    #     return sql.transResEq(ee1, ee2, tt)


class Oa(Op):
    pass


class Plus(Oa):
    def __init__(self, e1, e2):
        super(Plus, self).__init__("+", e1, e2)

    # def doOperation(self, v1, v2, sql: Engine):
    #     return self.doPlus(v1, v2, sql)
    #
    # def getCandidateTypes(self, sql):
    #     return sql.get_addition()
    #
    # def doPlus(self, v1, v2, sql):
    #     r = v1.erase() + v2.erase()
    #     return BValue(r)
    #
    # def getResultType(self, sql, rt):
    #     return sql.resTypePlus(rt)
    #
    # def getTransResult(self, sql, ee1, ee2, tt):
    #     return Plus(Ascr(ee1, tt[0]), Ascr(ee2, tt[1]))

