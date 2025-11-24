from interpreter.syntax.type.RelationType import RelationType, NameType

from interpreter.syntax.expression.BValue import *




def changeb(v):
    if v.erase() == 0:
        return False
    elif v.erase() == 1:
        return True
    elif v.erase() == None:
        return False
    else:
        return v.erase()


# Beta for projection
class Beta:
    def __init__(self, aliases):
        self.aliases = aliases

    def __str__(self):
        return ",".join(map(lambda a: str(a.e) + " as " + str(a.name), self.aliases))

    def __eq__(self, other):
        if isinstance(other, Beta):
            return self.aliases == other.aliases
        return False

    def expressions(self):
        return list(map(lambda a: a.e, self.aliases))

    def names(self):
        return list(map(lambda a: a.name, self.aliases))


    def typecheck(self, dbt, tablet, sql):
        res = []
        # print(self.aliases)
        for aliase in self.aliases:
            # print(aliase.e.typecheck(tablet, sql))
            res += [(NameType(aliase.name, aliase.e.typecheck(dbt, tablet, sql)))]
            # print(aliase.e) # here
            # print(res)
            # print(NameType(aliase.name, aliase.e.typecheck(tablet, sql)))
            # print(aliase.e.typecheck(tablet, sql))

        # print(TableType(res))
        return RelationType(res)

    def get_col_names(self):
        return list(map(lambda a: a.name, self.aliases))
    
    def trans(self, dbt, tablet, sql):
        return Beta(list(map(lambda a: a.trans(dbt, tablet, sql), self.aliases)) )

    def getLastE(self):
        if self.aliases[-1]:
            return self.aliases[-1].e
        else:
            raise Exception("list of aliases is empty")

    def getLastName(self):
        if self.aliases[-1]:
            return self.aliases[-1].name
        else:
            raise Exception("list of aliases is empty")


class Alias:
    def __init__(self, e, name):
        self.e = e
        self.name = name

    def __str__(self):
        return str(self.e) + " as " + str(self.name)

    def __eq__(self, other):
        if isinstance(other, Alias):
            return self.e == other.e and self.name == other.name
        return False

    def typecheck(self, dbt, tablet, sql):
        t = self.e.typecheck(dbt, tablet, sql)
        if t != BType():
            return RelationType([NameType(self.name, t)])
        else:
            raise Exception("Type checking fails!")

    def get_col_names(self):
        return [self.name]
    
    def trans(self, dbt, tablet, sql):
        ee = self.e.trans(dbt, tablet, sql)
        return Alias(ee, self.name)

# print(Beta([Alias(Real(1) , "a"), Alias(Real(2), "b")]))


# Queries
class Query:
    def run(self, db, sql):
        pass

    def typecheck(self, dbt, sql):
        pass

    def get_col_names(self):
        pass

    def trans(self, dbt, sql):
        pass
    
    def getBeta(self):
        raise Exception("Proj expected")


class Rel(Query):
    def __init__(self, tablename, attrnames):
        super().__init__()
        self.tablename = tablename
        self.attrnames = attrnames

    def __str__(self):
        return "Rel(" + str(self.tablename) + ", " + str(self.attrnames) + ")"

    def __eq__(self, other):
        return self.tablename == other.tablename and self.attrnames == other.attrnames
    
    def run(self, db, sql):
        # tbv = db[self.tablename]
        # for r in tbv.rows:
        #     for i,rawvalue in enumerate(r):
        #         c = BValue(rawvalue)
        #         c.unknown = False
        #         r[i] = c
                # if type(rawvalue) == float:
                #     c = Real(rawvalue)
                #     c.unknown = False
                #     r[i] = c
                # elif type(rawvalue) == int:
                #     c = Natural(rawvalue)
                #     c.unknown = False
                #     r[i] = c
                # elif type(rawvalue) == str:
                #     c = SString(rawvalue)
                #     c.unknown = False
                #     r[i] = c
                # elif type(rawvalue) == bool:
                #     c = Boolean(rawvalue)
                #     c.unknown = False
                #     r[i] = Boolean(r)
        return db[self.tablename]

    def typecheck(self, dbt, sql):
        return dbt[self.tablename]

    def get_col_names(self):
        return self.attrnames
    
    def trans(self, dbt, sql):
        return Rel(self.tablename, self.attrnames)


class Proj(Query):
    def __init__(self, beta: Beta, query: Query):
        super().__init__()
        self.beta = beta
        self.query = query

    def __str__(self):
        return "(project "+ str(self.beta) + " from " + str(self.query) + ")"

    def __eq__(self, other):
        return self.beta == other.beta and self.query == other.query

    def run(self, db, sql):
        table = self.query.run(db, sql)
        #########################
        rowsvalue = list(map(lambda row: list(map(lambda e: e.run(db, row, table.cols, sql), self.beta.expressions())),
                             table.rows))
        return Table(self.beta.names(), rowsvalue)
        #############attempt############
        # rowsvalue = []
        # if table.rows == []:
        #     for e in self.beta.expressions():
        #         e.run(db, [], table.cols, sql)
        # else:
        #     rowsvalue = list(map(lambda row: list(map(lambda e: e.run(db, row, table.cols, sql), self.beta.expressions())),
        #                      table.rows))
        # return Table(self.beta.names(), rowsvalue)

    def typecheck(self, dbt, sql):
        tbt1 = self.query.typecheck(dbt, sql)
        # print("hi1 " + str(tbt1))
        tbt2 = RelationType(sql.removeUnk(tbt1.nametypes))
        # print("hi2 " + str(tbt2))
        tbt3 = self.beta.typecheck(dbt, tbt2, sql)
        # print("hi3 " + str(tbt3))
        return tbt3

    def get_col_names(self):
        return self.beta.get_col_names()

    def get_expressions(self):
        return self.beta.expressions()

    def update_expressions(self, es):
        for i, e in enumerate(es):
            self.beta.aliases[i].e = e
    
    def trans(self, dbt, sql):
        qq = self.query.trans(dbt, sql)
        # print(qq)
        tbt1 = self.query.typecheck(dbt, sql)
        # print(tbt1)
        tbt2 = RelationType(sql.removeUnk(tbt1.nametypes))
        beta2 = self.beta.trans(dbt, tbt2, sql)
        return Proj(beta2, qq)
    
    def getBeta(self):
        return self.beta.aliases
        

class Sel(Query):
    def __init__(self, cond, query):
        super().__init__()
        self.cond = cond
        self.query = query
        self.isnull_not_null = False

    def __str__(self):
        return "(select "+ " * " + " from " + str(self.query)  + " Where " + str(self.cond) + ")"

    def __eq__(self, other):
        return self.cond == other.cond and self.query == other.query

    def run(self, db, sql):
        table = self.query.run(db, sql)

        ######################prv###
        # if table.rows == []:
        #     return Table(table.cols, [])
        # else:
        #     return Table(table.cols, list(filter(lambda row: changeb(self.cond.run(db, row, table.cols, sql)), table.rows)))
        #########################
        return Table(table.cols,list(filter(lambda row: changeb(self.cond.run(db, row, table.cols, sql)), table.rows)))


    def typecheck(self, dbt, sql):
        tbt = self.query.typecheck(dbt, sql)
        t = self.cond.typecheck(dbt, tbt, sql)
        sql.UImCast(self.cond, t, BType())
        # print(t)
        if sql.tag in ["Sqlite","Mysql"]:
            return tbt
        elif t.tag == "Bool":
            return tbt
        else:
            raise Exception("Program does not type check")

    def get_col_names(self):
        return self.query.get_col_names()

    def get_expressions(self):
        return self.query.get_expressions()

    def update_expressions(self, es):
        return self.query.update_expressions(es)
    
    def trans(self, dbt, sql):
        qq = self.query.trans(dbt, sql)
        cond2 = self.cond.trans(dbt, self.query.typecheck(dbt, sql), sql)
        return Sel(cond2, qq)


class Setop(Query):
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
            # rows = l.rows + (list(filter(lambda x: not (x in l.rows), r.rows)))
            # rows = list(set(tuple(sublist) for sublist in rows))
            # rows = [list(item) for item in rows]
            # return Table(l.cols, rows)
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
            # rows = (list(filter(lambda x: x in r.rows, l.rows)))
            # rows = list(set(tuple(sublist) for sublist in rows))
            # rows = [list(item) for item in rows]
            # return Table(l.cols, rows)
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
            # rows = (list(filter(lambda x: not (x in r.rows), l.rows)))
            # rows = list(set(tuple(sublist) for sublist in rows))
            # rows = [list(item) for item in rows]
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
            return Setop(self.op, Proj(Beta(rbeta1), ll.query), Proj(Beta(rbeta2), rr.query))


class Table:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows

    def __str__(self):      
        _str = ' | '.join(self.cols)+"\n"
        _str += '------------------------\n'
        _str += '\n'.join(list(map(lambda x: ' | '.join(map(lambda y: str(y), x)), self.rows)))
        return _str

    def __eq__(self, other):
        return self.cols == other.cols and self.rows == other.rows

# print(Ascr(Boolean(True), BType()))
# print(TableType({"1":"1", "2":"2"}))
# print(Cast(1,RType()))

# print(Name("name").typecheck(TableType({"name":SType(),"age":ZType()}), "Postgres"))

# print(Boolean(True).typecheck(TableType({"a": "int", "b":"str"}),"Postgres" ))


# print(Name("name").typecheck(TableType({"name":SType(),"age":ZType()}), "Postgres"))

