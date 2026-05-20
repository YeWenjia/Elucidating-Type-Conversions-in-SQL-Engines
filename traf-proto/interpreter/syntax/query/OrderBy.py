"""OrderBy query - ORDER BY clause"""

from interpreter.syntax.query.Query import Query
from interpreter.syntax.Table import Table
from interpreter.syntax.Alias import Alias
from interpreter.syntax.Beta import Beta


class OrderBy(Query):
    """
    ORDER BY query: sorts result rows by specified expressions.
    
    Handles queries like:
        SELECT name, age FROM table ORDER BY age DESC
        SELECT name FROM table GROUP BY name ORDER BY COUNT(*) DESC
    
    order_specs is a list of (expression, direction) tuples:
        expression: Beta expression (column ref, aggregate, arithmetic, etc.)
        direction: 'ASC' or 'DESC'
    """
    def __init__(self, query: Query, order_specs: list):
        super().__init__()
        self.query = query
        self.order_specs = order_specs  # [(expression, 'ASC'|'DESC'), ...]

    def __str__(self):
        specs = ", ".join(f"{expr} {direction}" for expr, direction in self.order_specs)
        return f"ORDER BY ({self.query}) [{specs}]"

    def __eq__(self, other):
        if isinstance(other, OrderBy):
            return self.query == other.query and self.order_specs == other.order_specs
        return False

   

    def typecheck(self, dbt, sql):
        """
        Type of ORDER BY is the same as the type of the subquery.
        ORDER BY doesn't change the schema, only reorders rows.
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
        # Transform order expressions
        tbt = self.query.typecheck(dbt, sql)
        transformed_specs = []
        for expr, direction in self.order_specs:
            # expr is typically an Alias, transform it
            if hasattr(expr, 'trans'):
                transformed_expr = expr.trans(dbt, tbt, sql)
            else:
                transformed_expr = expr
            transformed_specs.append((transformed_expr, direction))
        return OrderBy(translated_query, transformed_specs)

    def getBeta(self):
        return self.query.getBeta()
