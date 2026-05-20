"""Setop query - set operations (UNION, INTERSECT, EXCEPT, CROSS JOIN)"""

from interpreter.syntax.query.Query import Query
from interpreter.syntax.Table import Table
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.Alias import Alias
from interpreter.syntax.Beta import Beta


class Setop(Query):
    """Set operation query node - implements UNION, INTERSECT, EXCEPT, and CROSS JOIN"""
    
    def __init__(self, op, l: Query, r: Query):
        super().__init__()
        self.op = op
        self.l = l
        self.r = r

    def __str__(self):
        return "("+str(self.l)+" "+str(self.op)+" "+str(self.r)+")"

    def __eq__(self, other):
        return self.op == other.op and self.l == other.l and self.r == other.r

    def run(self, db, sql):
        l = self.l.run(db, sql)
        r = self.r.run(db, sql)
        if self.op == "X":
            result = []
            for i in l.rows:
                for j in r.rows:
                    result.append(i + j)
            return Table(l.cols + r.cols, result)
        elif self.op == "∪":
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

        elif self.op == "∩":
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
        elif self.op == "-":
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

    def typecheck(self, dbt, sql):
        if self.op == "X":
            left_cols = self.l.get_col_names()
            right_cols = self.r.get_col_names()
            com = list(set(left_cols).intersection(right_cols))
            if com == []:
                tbt1 = self.l.typecheck(dbt, sql)
                tbt2 = self.r.typecheck(dbt, sql)
                return RelationType(tbt1.nametypes + tbt2.nametypes)
            else:
                raise Exception("Program do not type check")
        elif self.op in ["∪", "∩", "-"]:
            beta1 = self.l.getBeta()
            beta2 = self.r.getBeta()
            
            tt1 = self.l.typecheck(dbt, sql).nametypes
            tt2 = self.r.typecheck(dbt, sql).nametypes
            
            def getSetOperator(t):
                e1 = t[0].e
                e2 = t[1].e
                t1 = t[2].type
                t2 = t[3].type
                return (t[2].name, sql.biconv(e1, t1, e2, t2))

            if len(beta1) == len(beta2):
                try:
                    zipped = zip(beta1, beta2, tt1, tt2)
                    return RelationType(list(map(lambda y: NameType(y[0], y[1]), map(lambda x: getSetOperator(x), list(zipped)))))
                except ValueError:
                    raise Exception('They do not have the same number of columns!')
            else:
                raise Exception('They do not have the same number of columns!')

    def get_col_names(self):
        if self.op == "X":
            rel1 = self.l
            rel2 = self.r
            left = self.l.get_col_names()
            right = self.r.get_col_names()
            return left + right
        elif self.op in ["∪", "∩", "-"]:
            return self.l.get_col_names()

    def get_expressions(self):
        if self.op == "X":
            left = self.l.get_expressions()
            right = self.r.get_expressions()
            return left + right
        elif self.op in ["∪", "∩", "-"]:
            return self.l.get_expressions()

    def update_expressions(self, es):
        if self.op == "X":
            self.l.update_expressions(es)
            self.r.update_expressions(es)
        elif self.op in ["∪", "∩", "-"]:
            return self.l.update_expressions(es)

    def trans(self, dbt, sql):
        if self.op == "X":
            ll = self.l.trans(dbt, sql)
            rr = self.r.trans(dbt, sql)
            return Setop(self.op, ll, rr)
        else:
            beta1 = self.l.getBeta()
            beta2 = self.r.getBeta()

            tt1 = self.l.typecheck(dbt, sql).nametypes
            tt2 = self.r.typecheck(dbt, sql).nametypes

            ll = self.l.trans(dbt, sql)
            rr = self.r.trans(dbt, sql)

            bbeta1 = ll.getBeta()
            bbeta2 = rr.getBeta()

            def getSetOperator(t):
                e1 = t[0].e
                e2 = t[1].e
                t1 = t[2].type
                t2 = t[3].type
                return sql.biconv(e1, t1, e2, t2)

            tlist = list(map(lambda x: getSetOperator(x), list(zip(beta1, beta2, tt1, tt2))))
            rbeta1 = list(map(lambda x, y: Alias((sql.insertAscr(x.e, y)), x.name), bbeta1, tlist))
            rbeta2 = list(map(lambda x, y: Alias((sql.insertAscr(x.e, y)), x.name), bbeta2, tlist))
            
            # Import Proj here to avoid circular import
            from interpreter.syntax.query.Proj import Proj
            return Setop(self.op, Proj(Beta(rbeta1), ll.query), Proj(Beta(rbeta2), rr.query))
