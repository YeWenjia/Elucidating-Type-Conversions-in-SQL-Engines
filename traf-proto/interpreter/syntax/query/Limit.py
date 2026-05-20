"""Limit query - LIMIT clause"""

from interpreter.syntax.query.Query import Query
from interpreter.syntax.Table import Table


class Limit(Query):
    """
    LIMIT query: limits the number of rows returned, optionally with offset.
    
    Handles queries like:
        SELECT name FROM table LIMIT 10
        SELECT name FROM table LIMIT 10 OFFSET 5
    """
    def __init__(self, query: Query, limit_count: int, offset: int = 0):
        super().__init__()
        self.query = query
        self.limit_count = limit_count
        self.offset = offset

    def __str__(self):
        offset_str = f" OFFSET {self.offset}" if self.offset > 0 else ""
        return f"LIMIT ({self.query}) {self.limit_count}{offset_str}"

    def __eq__(self, other):
        if isinstance(other, Limit):
            return (self.query == other.query and 
                    self.limit_count == other.limit_count and
                    self.offset == other.offset)
        return False

    def typecheck(self, dbt, sql):
        """
        Type of LIMIT is the same as the type of the subquery.
        LIMIT doesn't change the schema, only limits rows.
        """
        return self.query.typecheck(dbt, sql)

    def get_col_names(self):
        return self.query.get_col_names()

    def get_expressions(self):
        return self.query.get_expressions()

    def update_expressions(self, es):
        self.query.update_expressions(es)

    def trans(self, dbt, sql):
        translated_query = self.query.trans(dbt, sql)
        return Limit(translated_query, self.limit_count, self.offset)

    def getBeta(self):
        return self.query.getBeta()
