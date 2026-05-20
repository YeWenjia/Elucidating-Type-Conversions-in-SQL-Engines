"""Rel query - table reference"""

from interpreter.syntax.query.Query import Query


class Rel(Query):
    """Table reference query node"""
    
    def __init__(self, tablename: str, attrnames: list[str]):
        super().__init__()
        self.tablename: str = tablename
        self.attrnames: list[str] = attrnames

    def __str__(self):
        return "Rel(" + str(self.tablename) + ", " + str(self.attrnames) + ")"

    def __eq__(self, other):
        return self.tablename == other.tablename and self.attrnames == other.attrnames
    
    def run(self, db, sql):
        return db[self.tablename]

    def typecheck(self, dbt, sql):
        return dbt[self.tablename]

    def get_col_names(self):
        return self.attrnames
    
    def trans(self, dbt, sql):
        return Rel(self.tablename, self.attrnames)
