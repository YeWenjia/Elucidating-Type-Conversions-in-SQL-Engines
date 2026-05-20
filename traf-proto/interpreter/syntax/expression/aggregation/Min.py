from interpreter.syntax.expression.Expression import Expr
from interpreter.syntax.expression.BValue import BValue


class Min(Expr):
    """
    Aggregate function: MIN(expr)
    Returns the minimum value in the expression
    """
    
    def __init__(self, expr):
        """
        Initialize Min aggregate function.
        
        Args:
            expr: Expression to find minimum of
        """
        super().__init__()
        # Check for nested aggregates
        from interpreter.syntax.expression.aggregation import check_no_nested_aggregates
        check_no_nested_aggregates(expr)
        self.expr = expr
        self.isnull = False
        self.isnull_not_null = False
    
    def __str__(self):
        return f"MIN({str(self.expr)})"
    
    def __eq__(self, other):
        if not isinstance(other, Min):
            return False
        return self.expr == other.expr
    
    def run(self, db, row, attrnames, sql):
        """
        Placeholder run method for aggregate context.
        
        Note: Actual aggregation will be handled by GroupBy.run() which will
        pass groups of rows instead of single rows. This method is here for
        interface compliance but shouldn't be called in normal aggregate usage.
        """
        raise NotImplementedError("Min.run should not be called directly; aggregation is handled in GroupBy.run()")
    
    def typecheck(self, dbt, tablet, sql):
        """
        Type check the MIN expression.
        
        MIN returns the same type as its input expression.
        Works on any comparable type (numeric, string, etc.).
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            The type of the input expression
        """
        # Type check the inner expression and return its type
        expr_type = self.expr.typecheck(dbt, tablet, sql)
        return expr_type
    
    def trans(self, dbt, tablet, sql):
        """
        Transform the MIN expression (for query transformation/optimization).
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            Transformed Min expression
        """
        # Transform the inner expression
        transformed_expr = self.expr.trans(dbt, tablet, sql)
        return Min(transformed_expr)
