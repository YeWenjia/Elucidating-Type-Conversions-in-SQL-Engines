"""Proj query - projection/SELECT"""

from interpreter.syntax.query.Query import Query
from interpreter.syntax.Beta import Beta
from interpreter.syntax.Table import Table
from interpreter.syntax.type.RelationType import RelationType


class Proj(Query):
    """Projection query node - implements SELECT clause"""
    
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
