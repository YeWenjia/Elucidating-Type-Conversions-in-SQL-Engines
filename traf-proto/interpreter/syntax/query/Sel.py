"""Sel query - selection/WHERE clause"""

from interpreter.syntax.query.Query import Query
from interpreter.syntax.Table import Table
from interpreter.syntax.utils import changeb


class Sel(Query):
    """Selection query node - implements WHERE clause"""
    
    def __init__(self, cond, query):
        super().__init__()
        self.cond = cond
        self.query = query
        self.isnull_not_null = False

    def __str__(self):
        return "(select "+ str(self.query)  + " Where " + str(self.cond) + ")"

    def __eq__(self, other):
        return self.cond == other.cond and self.query == other.query

    def run(self, db, sql):
        table = self.query.run(db, sql)
        return Table(table.cols, list(filter(lambda row: changeb(self.cond.run(db, row, table.cols, sql)), table.rows)))

    def typecheck(self, dbt, sql):
        from interpreter.syntax.expression.BValue import BType
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
