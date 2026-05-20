"""
ScalarSubquery: A subquery that must return exactly one row and one column.

Used for scalar comparisons like:
  WHERE age = (SELECT MIN(age) FROM student)
"""

from interpreter.syntax.expression.BExpr import BExpr


class ScalarSubquery(BExpr):
    """
    A scalar subquery wraps a Query and ensures it returns exactly one value.
    This is used in comparisons like: expr = (SELECT ...)
    """
    
    def __init__(self, query):
        super().__init__()
        self.query = query
        self.isnull = False  # Required for Op compatibility
        self.isnull_not_null = False
    
    def __str__(self):
        return f"(SCALAR {self.query})"
    
    def __eq__(self, other):
        return isinstance(other, ScalarSubquery) and self.query == other.query
