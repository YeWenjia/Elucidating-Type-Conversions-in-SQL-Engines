from interpreter.AbstractOps import AbstractOps
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression import Expression
from interpreter.syntax.expression.NName import NName
from interpreter.syntax.expression.Op import Op
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.type.RelationType import *
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.Or import Or
from interpreter.syntax.type.ValueType import *


class Runtime:
    # ops: AbstractOps

    def __init__(self, ops):
        self.ops = ops

    def changeb(self, v):
        if v.erase() == 0:
            return False
        elif v.erase() == 1:
            return True
        else:
            return v.erase()

    def run_query(self, db, q: Query) -> Table:
        # print(q)
        match q:
            case Rel():
                # print(f"case Rel: {q}")
                return db[q.tablename]
            case Proj():
                table = self.run_query(db, q.query)
                es = q.beta.expressions()
                rowsvalue = list(map(lambda row: list(map(lambda e: self.run_expr(row, table.cols, e), es)),
                                     table.rows))
                names = q.beta.names()
                return Table(names, rowsvalue)
            case Sel():
                # print(f"case Sel: {q}")
                table = self.run_query(db, q.query)
                return Table(table.cols,
                             list(filter(lambda row: self.changeb(self.run_expr(row, table.cols, q.cond)), table.rows)))
            case Setop():
                l = self.run_query(db, q.l)
                r = self.run_query(db, q.r)
                match q.op:
                    case "X":
                        result = []
                        for i in l.rows:
                            for j in r.rows:
                                result.append(i + j)
                        return Table(l.cols + r.cols, result)
                    case "∪":
                        def eraseRow(r):
                            res = []
                            for vc in r:
                                res.append(vc.v)
                            return res

                        def eraseRows(rs):
                            res = []
                            for r in rs:
                                res.append(eraseRow(r))
                            return res

                        rows = l.rows + (list(filter(lambda x: not (eraseRow(x) in eraseRows(l.rows)), r.rows)))
                        res = [lst for i, lst in enumerate(rows) if eraseRow(lst) not in eraseRows(rows[:i])]
                        return Table(l.cols, res)
                    case "∩":
                        def eraseRow(r):
                            res = []
                            for vc in r:
                                res.append(vc.v)
                            return res

                        def eraseRows(rs):
                            res = []
                            for r in rs:
                                res.append(eraseRow(r))
                            return res

                        rows = (list(filter(lambda x: eraseRow(x) in eraseRows(r.rows), l.rows)))
                        res = [lst for i, lst in enumerate(rows) if eraseRow(lst) not in eraseRows(rows[:i])]
                        return Table(l.cols, res)
                    case "-":
                        def eraseRow(r):
                            res = []
                            for vc in r:
                                res.append(vc.v)
                            return res

                        def eraseRows(rs):
                            res = []
                            for r in rs:
                                res.append(eraseRow(r))
                            return res

                        rows = (list(filter(lambda x: not (eraseRow(x) in eraseRows(r.rows)), l.rows)))
                        res = [lst for i, lst in enumerate(rows) if eraseRow(lst) not in eraseRows(rows[:i])]
                        return Table(l.cols, res)
        raise Exception(f"Running Query Error: {q}")

    def run_expr(self, row, attrnames, e: Expression) -> BValue:
        match e:
            case BValue():  # (Tv)
                return BValue(e.v, e.use_decimal)
            case NName():  # (TN)
                return row[attrnames.index(e.name)]
            case BNeg():
                bp = self.run_expr(row, attrnames, e.b)
                match bp.erase():
                    case 1:
                        return Natural(0)
                    case 0:
                        return Natural(1)
                    case _:
                        return Boolean(not bp.erase())
            case Ascr():
                ep = self.run_expr(row, attrnames, e.e)
                return self.ops.cast(ep, e.t)
            case Op():
                # print(f"running operation {e.op}", [e])
                v1 = self.run_expr(row, attrnames, e.e1)
                v2 = self.run_expr(row, attrnames, e.e2)
                # print(f"of {e.op}, v1: {v1}, v2: {v2}")
                v = self.ops.apply(e.op, v1, v2)
                # print(f"result of {e.op} is", v)
                return v
            case And():
                v1 = self.run_expr(row, attrnames, e.l)
                v2 = self.run_expr(row, attrnames, e.r)
                if (v1.erase() == 0):
                    return v1
                elif (v1.erase() == False):
                    return v1
                return v2
            case Or():
                v1 = self.run_expr(row, attrnames, e.l)
                v2 = self.run_expr(row, attrnames, e.r)
                if (v1.erase() == 1):
                    return v1
                elif (v1.erase() == True):
                    return v1
                return v2
        raise Exception(f"Not implemented Expression Error: {e}")

    def apply(self, op, v1: BValue, v2: BValue) -> BValue:
        """
        This function corresponds to the apply
        """
        raise Exception(f"'Apply' function not implemented")
