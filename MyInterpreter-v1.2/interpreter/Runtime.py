from interpreter.AbstractOps import AbstractOps
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression import Expression
from interpreter.syntax.expression.IsNull import IsNull
from interpreter.syntax.expression.NName import NName
from interpreter.syntax.expression.Op import Op
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.type.RelationType import *
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.Or import Or
from interpreter.syntax.expression.Empty import Empty
from interpreter.syntax.expression.Ins import Ins


class Runtime:
    # ops: AbstractOps

    def __init__(self, ops):
        self.ops = ops



    def changeb(self, v):
        if v.erase() == 0:
            return False
        elif v.erase() == 1:
            return True
        elif v.erase() is None:
            return False
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
                # if isinstance(q.query, Sel) and q.query.isnull_not_null and self.ops.check_optimization():
                #     es = q.beta.expressions()
                #     def safe_eval(e, row):
                #         try:
                #             return self.run_expr(db, row, table.cols, e)
                #         except:
                #             return Nullv(None)
                #
                #     rowsvalue = list(map(
                #         lambda row: list(map(lambda e: safe_eval(e, row), es)), table.rows))
                #     return Table(q.beta.names(), rowsvalue)
                es = q.beta.expressions()
                rowsvalue = list(map(lambda row: list(map(lambda e: self.run_expr(db, row, table.cols, e), es)),
                                     table.rows))
                names = q.beta.names()
                return Table(names, rowsvalue)
            case Sel():
                # print(f"case Sel: {q}")
                table = self.run_query(db, q.query)
                q.isnull_not_null = q.cond.isnull_not_null

                # deal with null:
                condp = q.cond
                if condp.isnull:
                    condp = Nullv(None)

                ###################

                # tempt = Table(table.cols, list(filter(lambda row: self.changeb(self.run_expr(db, row, table.cols, q.cond)), table.rows)))
                # Step 1: Get the column definitions from the table
                columns = table.cols

                # Step 2: Define a function to check if each row satisfies the condition
                def row_satisfies_condition(row):
                    # 2a: Execute the condition expression on the current row
                    expr_result = self.run_expr(db, row, table.cols, condp)

                    # 2b: Convert the result to a boolean value
                    boolean_result = self.changeb(expr_result)

                    return boolean_result

                # Step 3: Iterate through all rows and filter those that satisfy the condition
                filtered_rows = []
                for row in table.rows:
                    if row_satisfies_condition(row):
                        filtered_rows.append(row)

                # Step 4: Create a new table with the original columns and filtered rows
                tempt = Table(columns, filtered_rows)
                return tempt
            case Setop():
                l = None
                r = None
                l_error = None
                r_error = None

                try:
                    l = self.run_query(db, q.l)
                except Exception as e:
                    l_error = e

                try:
                    r = self.run_query(db, q.r)
                except Exception as e:
                    r_error = e

                if l is not None and l.rows == [] and self.ops.check_optimization() and (q.op in ("∩", "-")):
                    return l
                # elif r is not None and r.rows == [] and self.ops.check_optimization() and (q.op in ("∩", "-")):
                #     return r
                elif l_error is not None:
                    raise Exception(l_error)
                elif r_error is not None:
                    raise Exception(r_error)
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

    def run_expr(self, db, row, attrnames, e: Expression) -> BValue:
        match e:
            case BValue():  # (Tv)
                return BValue(e.v, e.use_decimal)
            case NName():  # (TN)
                return row[attrnames.index(e.name)]
            case BNeg():
                bp = self.run_expr(db, row, attrnames, e.b)
                match bp.erase():
                    case 1:
                        return Natural(0)
                    case 0:
                        return Natural(1)
                    case None:
                        return Nullv(None)
                    case _:
                        return Boolean(not bp.erase())
            case Ascr():
                ep = self.run_expr(db, row, attrnames, e.e)
                return self.ops.cast(ep, e.t)
            case Op():
                # print(f"running operation {e.op}", [e])
                v1 = self.run_expr(db, row, attrnames, e.e1)
                v2 = self.run_expr(db, row, attrnames, e.e2)
                # print(f"of {e.op}, v1: {v1}, v2: {v2}")
                v = self.ops.apply(e.op, v1, v2)
                # print(f"result of {e.op} is", v)
                return v
            case And():
                v1 = self.run_expr(db, row, attrnames, e.l)
                v2 = self.run_expr(db, row, attrnames, e.r)
                if (v1.erase() == 0):
                    return v1
                elif (v1.erase() == False):
                    return v1
                elif(v1.v is None and v2.v != False):
                    # vv = self.ops.boolean_value(False) here i change for null
                    return v1
                # elif(v2.v is None):
                #     return v2
                return v2
            case Or():
                v1 = self.run_expr(db, row, attrnames, e.l)
                v2 = self.run_expr(db, row, attrnames, e.r)
                if (v1.erase() == 1):
                    return v1
                elif (v1.erase() == True):
                    return v1
                elif(v1.v is None and v2.v != True):
                    return v1
                return v2
            case Empty():
                ep = e.q
                ep.beta = Beta([Alias(Natural(1), '1')])
                t = self.run_query(db, ep)
                b = self.ops.doEmpty(t)
                return b
            case Ins():
                r = []
                table = self.run_query(db, e.q)
                if table.rows == []:
                    return BValue(False)
                else:
                    for i, e in enumerate(e.es):
                        v = self.run_expr(db, row, attrnames, e)
                        r.append(v)
                    b = self.ops.doIn(r, table.rows)
                    return b
            case IsNull():
                v = self.run_expr(db, row, attrnames, e.e)
                return self.ops.isnull_res(v)


        raise Exception(f"Not implemented Expression Error: {e}")

    # def apply(self, op, v1: BValue, v2: BValue) -> BValue:
    #     """
    #     This function corresponds to the apply
    #     """
    #     raise Exception(f"'Apply' function not implemented")

    # def doEmpty(self, t):
    #     return BValue(True if t.rows != [] else False)
    #
    # def doIn(self, es, rs, db, row, attrnames, sql):
    #     for r in rs:
    #         eq = True
    #         for i, e in enumerate(es):
    #             rr = r[i]
    #             bb = self.apply("=", e, rr)
    #             if not (bb.erase()):
    #                 eq = False
    #                 break
    #         if eq:
    #             return BValue(eq)
    #     return BValue(False)

#
# 1. without any simplification
# 2. with all simplification