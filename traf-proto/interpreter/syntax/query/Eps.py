"""Eps query - DISTINCT (duplicate elimination)"""

from interpreter.syntax.query.Query import Query
from interpreter.syntax.Table import Table


class Eps(Query):
    """
    Duplicate elimination (DISTINCT)
    Removes duplicate rows from the result of the subquery.
    """
    def __init__(self, query: Query):
        super().__init__()
        self.query = query

    def __str__(self):
        return f"ε({self.query})"

    def __eq__(self, other):
        if isinstance(other, Eps):
            return self.query == other.query
        return False



    def typecheck(self, dbt, sql):
        """
        Type of DISTINCT is the same as the type of the subquery.
        DISTINCT doesn't change the schema, only removes duplicates.
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
        return Eps(translated_query)

    def getBeta(self):
        return self.query.getBeta()
