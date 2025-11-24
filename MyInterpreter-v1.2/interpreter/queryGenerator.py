import random
import string
from interpreter.Parser import *
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.ValueType import *
import copy
# dbt = {
#     "tablea": TableType([NameType("name", SType()), NameType("age", ZType())]),
#     "tableb": TableType([NameType("fullname", SType()), NameType("realage", ZType())]),
#     "tablec": TableType([NameType("newage", ZType()), NameType("newname", SType())])
# }


dbt = {
    "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
    "TB": RelationType([NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
    "TC": RelationType([NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
}
totalsub = 0
totalcol = 0
totalin = 0
totalexist = 0

class GenTable:
    def __init__(self, tablename, colnames):
        self.tablename = tablename
        self.colnames = colnames

class GenColumns:
    def __init__(self, colnames):
        self.colnames = colnames

class GenQueryResult:
    def __init__(self, querystr, gentables):
        self.querystr = querystr
        self.gentables = gentables
        # self.totalsub = totalsub

    def __str__(self):
        return self.querystr

    # def incTotalSub(self):
    #     return GenQueryResult(self.querystr, self.gentables, self.totalsub+1)

    # def __str__(self):
    # list_with_duplicates = self.querystr.split(",")
    # list_without_duplicates = list(set(list_with_duplicates))
    # string_without_duplicates = ",".join(list_without_duplicates)
    # return string_without_duplicates


class GenOptions:
    # GenOptions("", 0, 1, 0, 1, 0, 1, 0, 1, "", 0, 1, select=True, engine=engine)
    def __init__(self, engine, prefix="", depth=0, maxdepth=1, comp=0,
                 maxcomp=1, setdepth=0, maxset=1, sub=0, maxsub=1, prefixcol="", expr=0, maxexp=1, generateWhere=True,
                 simplification=True, innum=0, maxin=1, exnum=0, maxex=1, onlyname=False, with_null = True):
        self.prefix = prefix
        self.depth = depth
        self.maxdepth = maxdepth
        self.comp = comp
        self.maxcomp = maxcomp
        # current number of set operators generated
        self.setdepth = setdepth
        # maximum number of set operators allowed
        self.maxset = maxset
        self.sub = sub
        self.maxsub = maxsub
        self.prefixcol = prefixcol
        self.expr = expr
        self.maxexp = maxexp
        # True if we want to generate where in select from queries.
        self.generateWhere = generateWhere
        self.engine = engine
        # True if we are performing simplifications
        self.simplification = simplification
        self.with_null = with_null
        self.innum = innum
        self.maxin = maxin
        self.exnum = exnum
        self.maxex = maxex
        self.onlyname = onlyname


    def incDepth(self):
        newOpt = copy.deepcopy(self)
        newOpt.depth += 1
        return newOpt

    def incComp(self):
        newOpt = copy.deepcopy(self)
        newOpt.comp += 1
        return newOpt


    def incSet(self):
        newOpt = copy.deepcopy(self)
        newOpt.setdepth += 1
        return newOpt


    def incSub(self):
        newOpt = copy.deepcopy(self)
        newOpt.sub += 1
        return newOpt


    def incExp(self):
        newOpt = copy.deepcopy(self)
        newOpt.expr += 1
        return newOpt


    def withPrefix(self, prefix):
        newOpt = copy.deepcopy(self)
        newOpt.prefix = prefix
        return newOpt

    def withPrefixCol(self, prefixcol):
        newOpt = copy.deepcopy(self)
        newOpt.prefixcol = prefixcol
        return newOpt

    def incInnum(self):
        newOpt = copy.deepcopy(self)
        newOpt.innum += 1
        return newOpt

    def incEx(self):
        newOpt = copy.deepcopy(self)
        newOpt.exnum += 1
        return newOpt



def generateRel(opts):
    tablename = random.choice(list(db.keys()))
    alias = tablename + f"{opts.prefix}"
    return GenQueryResult(f"{tablename} {alias}",
                          [GenTable(alias, list(map(lambda x: x.name, dbt[tablename].nametypes)))])
    # return GenQueryResult(f"{tablename} AS {alias}", [GenTable(alias, list(map(lambda x: x.name, dbt[tablename].nametypes)))])


# def generateRel(opts):
#     tablename = random.choice(list(db.keys()))
#     return GenQueryResult(f"{tablename}", [GenTable(tablename, list(map(lambda x: x.name, dbt[tablename].nametypes)))])


def generateNumber():
    i = random.randint(0, 1)
    if i == 0:
        # return round(random.random() * 100, 1)
        return round(random.random() * 40, 1)+10.0
    else:
        return random.randint(-10, 10)


def generateString():
    i = random.randint(0, 1)
    if i == 0:
        return f"'{''.join(random.choices(string.ascii_lowercase, k=5))}'"
    else:
        return f"'{generateNumber()}'"


def generateValue():
    i = random.randint(0, 2)
    if i == 0:
        return generateNumber()
    elif i == 1:
        return f"NULL"
    else:
        return generateString()

def generateBValue():
    i = random.randint(0, 1)
    if i == 0:
        return generateNumber()
    else:
        return generateString()


def generateName(gqr):
    gentable = random.choice(gqr.gentables)
    # return f'{random.choice(gentable.colnames)}'
    return f'{gentable.tablename}.{random.choice(gentable.colnames)}'


def generateComparison(gqr, opts):

    if opts.simplification and opts.with_null:
        i = random.randint(0, 3)
    elif opts.simplification and not opts.with_null:
        i = random.randint(0, 2)
    elif not opts.simplification and opts.with_null:
        i = random.randint(0, 5)
    elif not opts.simplification and not opts.with_null:
        i = random.choice([0, 1, 2, 4, 5])

    if i == 0 or opts.comp >= opts.maxcomp or opts.innum >= opts.maxin or opts.exnum >= opts.maxex:
        j = random.randint(0, 1)
        if j == 0:
            return f"{generateExp(gqr, opts.incComp())} < {generateExp(gqr, opts.incComp())}"
        elif j == 1:
            return f"{generateExp(gqr, opts.incComp())} = {generateExp(gqr, opts.incComp())}"
    elif i == 1:
        if opts.simplification:
            opts.onlyname = True
        q = generateQuery(opts.incInnum())
        l = len(q.gentables.colnames)
        if l == 1 :
            if opts.simplification:
                cs = generateName(gqr)
                opts.onlyname = True
            else:
                cs = generateExp(gqr, opts)
            return f"{cs} IN ({q})"
        else:
            if opts.simplification:
                cs = [generateName(gqr) for jj in range(l)]
                res = ", ".join([c for c in cs])
                opts.onlyname = True
            else:
                cs = [generateExp(gqr, opts) for jj in range(l)]
                res = ", ".join([c for c in cs])
            return f"({res}) IN ({q})"
    elif i == 2:
        q = generateQuery(opts.incInnum())
        return f"EXISTS ({q})"
    elif i == 3:
        e = generateExp(gqr, opts)
        return f"({e} IS NULL)"
    elif i == 4:
        return f"({generateComparison(gqr, opts.incComp())} AND {generateComparison(gqr, opts.incComp())})"
    elif i == 5:
        return f"({generateComparison(gqr, opts.incComp())} OR {generateComparison(gqr, opts.incComp())})"

# SELECT CAST(TA1.height AS TEXT) AS col0, CAST(TC0.newheight AS INT) AS col1, '6.7' AS col2 FROM TC TC0,TA TA1 INTERSECT SELECT Sub1.col0 + Sub1.col0 AS col0 FROM (SELECT CAST(TC.newname AS INT) AS col0 FROM TC TC) As Sub1 WHERE Sub1.col0 IN (SELECT '99.3' AS col0 FROM (SELECT TC.newheight AS col0, TC.newname AS col1 FROM TC TC WHERE 'qfvyh' = 73.9) As Sub2)

def generateExp(gqr, opt):
    i = random.randint(0, 3)

    if i == 0 or opt.expr >= opt.maxexp:  # name
        return f"{generateName(gqr)}"
    elif i == 1 or opt.expr >= opt.maxexp:
        if opt.with_null: # value
            return f"{generateValue()}"
        else:
            return f"{generateBValue()}"
    elif i == 2:  # addition
        if opt.engine == "Mysql":
            return f"CAST({generateExp(gqr, opt.incExp())} AS DECIMAL(10,1)) + CAST({generateExp(gqr, opt.incExp())} AS DECIMAL(10,1))"
        else:
            return f"{generateExp(gqr, opt.incExp())} + {generateExp(gqr, opt.incExp())}"
    elif i == 3:  # cast
        j = random.randint(0, 2)
        if j == 0:
            if opt.engine == "Oracle":
                return f"CAST({generateExp(gqr, opt.incExp())} AS FLOAT)"
            else:
                return f"CAST({generateExp(gqr, opt.incExp())} AS DECIMAL(10,1))"
        elif j == 1:
            if opt.engine in ["Mssql", "Oracle"]:
                return f"CAST({generateExp(gqr, opt.incExp())} AS VARCHAR(255))"  # mssql oracle
            elif opt.engine == "Mysql":
                return f"CAST({generateExp(gqr, opt.incExp())} AS CHAR)"  # mysql
            else:
                return f"CAST({generateExp(gqr, opt.incExp())} AS TEXT)"
        elif j == 2:
            if opt.engine == "Mysql":
                return f"CAST({generateExp(gqr, opt.incExp())} AS SIGNED)"  # mysql
            else:
                return f"CAST({generateExp(gqr, opt.incExp())} AS INT)"

    # elif i == 2:
    #     return f"POWER({generateValue()},{generateValue()})"
    # elif i == 3:
    #     return f"SQRT({generateValue()})"


def generateCol(gqr, opt):
    if opt.onlyname == True and opt.simplification:
        e = generateName(gqr)
    else:
        e = generateExp(gqr, opt)
    return (f"{e} AS {'col'}{opt.prefixcol}", f"{'col'}{opt.prefixcol}")


def generateCols(gqr, opt):
    res = ""
    j = 0 if opt.simplification else random.randint(0, 2)

    cs = [generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}{i}')) for i in range(j+1)]
    #for i in range(j+1):
    #    c = generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}{0}'))
    # if i == 0:
    #res = c[0]
    # else:
    #     res = res + "," + c
    res = ", ".join([c[0] for c in cs])
    cols = [c[1] for c in cs]
    return GenQueryResult(res, GenColumns(cols))
    # i = random.randint(0,2)
    # if i==0:
    #     return generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}'))
    # elif i==1:
    #     return f"{generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}0'))},{generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}1'))}"
    # elif i==2:
    #     return f"{generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}a'))},{generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}b'))},{generateCol(gqr, opt.withPrefixCol(f'{opt.prefixcol}c'))}"


def generateCross(opts):
    q1 = generateFrom(opts.withPrefix(f"{opts.prefix}0"))
    q2 = generateFrom(opts.withPrefix(f"{opts.prefix}1"))
    return GenQueryResult(f"{q1.querystr},{q2.querystr}", q1.gentables + q2.gentables)


def generateSubquery(opts):
    q = generateQuery(opts)
    global totalsub
    totalsub = totalsub + 1
    #for tb in q.gentables:
    #    tb.tablename = f"Sub{totalsub}"
    #return GenQueryResult(f"({q}) As Sub{totalsub}", q.gentables)
    return GenQueryResult(f"({q}) Sub{totalsub}", [GenTable(f"Sub{totalsub}", q.gentables.colnames)])
    # return GenQueryResult(f"({q}) As Sub{totalsub}", [GenTable(f"Sub{totalsub}", q.gentables.colnames)])


# def generateWhere(gqr, opt):
#     i = random.randint(0, 2)
#     if i == 0 or opt.comp >= opt.maxcomp:
#         j = random.randint(0, 1)
#         if j == 0:
#             return f"{generateExp(gqr, opt.incComp())} < {generateExp(gqr, opt.incComp())}"
#         elif j == 1:
#             return f"{generateExp(gqr, opt.incComp())} = {generateExp(gqr, opt.incComp())}"
#     elif i == 1:
#         return f"{generateWhere(gqr, opt.incComp())} AND {generateWhere(gqr, opt.incComp())}"
#     elif i == 2:
#         return f"{generateWhere(gqr, opt.incComp())} OR {generateWhere(gqr, opt.incComp())}"
# elif i == 3:
#     return f"NOT ({generateWhere(gqr, opt.incComp())})"


def generateFrom(opts):
    i = random.randint(0, 1) if opts.simplification else random.randint(0, 2)
    if i == 0 or opts.depth >= opts.maxdepth or opts.sub >= opts.maxsub:
        return generateRel(opts.incDepth())
    elif i == 1:
        return generateCross(opts.incDepth())
    elif i == 2:
        return generateSubquery(opts.incSub())


def generateQuery(opts):
    i = random.randint(0, 1)
    # i = 0
    if opts.engine == "Mssql":
        i = 0
    if i == 0 or opts.setdepth >= opts.maxset:
        j = random.randint(0, 1)
        # j = 0
        # if j == 0 and opts.generateWhere and opts.engine != "Mssql":
        if j == 0 and opts.generateWhere:
            fromq = generateFrom(opts.incSet())
            where = generateComparison(fromq, opts.incSet())
            select = generateCols(fromq, opts.incSet())
            return GenQueryResult(f"""SELECT {select.querystr} FROM {fromq} WHERE {where}""", select.gentables)
        else:
            fromq = generateFrom(opts.incSet())
            select = generateCols(fromq, opts.incSet())
            return GenQueryResult(f"""SELECT {select.querystr} FROM {fromq}""", select.gentables)
    else:
        opts.incDepth()
        if opts.engine == "Mysql" :
            j = 0
        else:
            j = random.randint(0, 2)
        if j == 0:
            if opts.engine == "Mssql":
                opts.generateWhere = False
                q1 = generateQuery(opts.incSet())
                q2 = generateQuery(opts.incSet())
                return GenQueryResult(f"""{q1} UNION {q2}""", q1.gentables)
            else:
                q1 = generateQuery(opts.incSet())
                q2 = generateQuery(opts.incSet())
                return GenQueryResult(f"""{q1} UNION {q2}""", q1.gentables)
        elif j == 1:
            if opts.engine == "Oracle":
                q1 = generateQuery(opts.incSet())
                q2 = generateQuery(opts.incSet())
                return GenQueryResult(f"""{q1} MINUS {q2}""", q1.gentables)  # oracle
            elif opts.engine == "Mssql":
                if opts.simplification:
                    opts.generateWhere = False
                q1 = generateQuery(opts.incSet())
                q2 = generateQuery(opts.incSet())
                return GenQueryResult(f"""{q1} EXCEPT {q2}""", q1.gentables)
            else:
                q1 = generateQuery(opts.incSet())
                q2 = generateQuery(opts.incSet())
                return GenQueryResult(f"""{q1} EXCEPT {q2}""", q1.gentables)
        elif j == 2:
            if opts.engine == "Mssql":
                if opts.simplification:
                    opts.generateComparison = False
                q1 = generateQuery(opts.incSet())
                q2 = generateQuery(opts.incSet())
                return GenQueryResult(f"""{q1} INTERSECT {q2}""", q1.gentables)
            else:
                q1 = generateQuery(opts.incSet())
                q2 = generateQuery(opts.incSet())
                return GenQueryResult(f"""{q1} INTERSECT {q2}""", q1.gentables)


def generate(engine, simplification=True, with_null = True):
    opts = GenOptions(engine=engine, simplification=simplification, with_null = with_null)
    global totalsub
    totalsub = 0
    global totalcol
    totalcol = 0
    global totalin
    totalin = 0
    global totalexist
    totalexist = 0
    q = generateQuery(opts)
    # if opts.engine == "Oracle":
    #     return f"{q}"
    #
    # else:
    return f"{q};"


# print(generate("Postgres", True))


# from ((select 1) union (select 2)) as A;


