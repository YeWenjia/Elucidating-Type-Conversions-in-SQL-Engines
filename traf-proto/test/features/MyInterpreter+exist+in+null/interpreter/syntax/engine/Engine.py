from interpreter.syntax.expression.Expression import *
# from abc import ABC, abstractmethod
from interpreter.syntax.expression.BValue import *
from interpreter.syntax.expression.Ascr import *

# class Engine(ABC):
class Engine():
    def Compare(self, myrows, otherrows, sql):
        if len(myrows) == len(otherrows):
            result = []
            for myrow in myrows:
                # print("--myrow--")
                # print(myrow)
                for otherrow in otherrows:
                    # print("--otherrow--")
                    # print(otherrow)
                    # print("----")
                    ls = list(map(lambda x, y: sql.comparev(x.erase(),y), myrow, otherrow))
                    # print("--boolean list--")
                    # print(ls)
                    # print("-------------")
                    if False in ls:
                        continue
                    else:
                        otherrows.remove(otherrow)
                        # print(otherrows)
                        result.append(True)
                        # print("--result list--")
                        # print(result)
                        break
            # print("result:" + str(len(result)))
            # print("myrows:" + str(len(myrows)))
            if len(result) == len(myrows):
                return True
            else:
                return False
        else:
            return False

    def biconv(self, e1, t1, e2, t2):
        pass

    def overload(self, e1, e2, t1, t2, tlist):
        pass

    def ExCast(self, e, t1, t2):
        pass

    def BImCast(self, e1, e2, t1, t2, t3, t4):
        pass

    def UImCast(self, e, t1, t2):
        pass

    def upcastToInt(self, v):
        raise Exception("no conversion supports")


    def format(self, v):
        return v.erase()


    # @abstractmethod
    def getCandidateTypesLt(self):
        pass

    def doLt(self, v1, v2):
        return BValue(self.format(v1) < self.format(v2))

    # @abstractmethod
    def getCandidateTypesEq(self):
        pass

    def doEq(self, v1, v2):
        return BValue(self.format(v1) == self.format(v2))

    def doEmpty(t):
        return BValue(t != [])

    def bvalue_eq(self, vs1, vs2):
        eq = False
        for i, v in enumerate(vs1):
            v2 = vs2[i].erase()
            v1 = v.erase()
            if v1 == v2:
                eq = True
                break
        return eq

    def doIn(self, es, rs, db, row, attrnames, sql):
        for r in rs:
            eq = True
            for i, e in enumerate(es):
                rr = r[i]
                bb = sql.doEq(e, rr)
                if not(bb.erase()):
                    eq = False
                    break
            if eq:
                return BValue(eq)
        return BValue(False)

    def getCandidateTypesAnd(self):
        return [(BType(), BType(), BType())]

    def getCandidateTypesOr(self):
        return [(BType(), BType(), BType())]

    def resTypeLor(self):
        return BType()

    def resTypeLand(self):
        return BType()

    def removeUnk(self, nametypes):
        return nametypes


    def icast(self, v, t):
        return v.upcast(t, self)


    def insertAscr(self, e, t):
        return Ascr(e, t)





