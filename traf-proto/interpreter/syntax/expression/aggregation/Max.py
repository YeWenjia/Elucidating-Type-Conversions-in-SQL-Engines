from interpreter.syntax.expression.Expression import Expr
from interpreter.syntax.expression.BValue import BValue


class Max(Expr):
    """
    Aggregate function: MAX(expr)
    Returns the maximum value in the expression
    """
    
    def __init__(self, expr):
        """
        Initialize Max aggregate function.
        
        Args:
            expr: Expression to find maximum of
        """
        super().__init__()
        # Check for nested aggregates
        from interpreter.syntax.expression.aggregation import check_no_nested_aggregates
        check_no_nested_aggregates(expr)
        self.expr = expr
        self.isnull = False
        self.isnull_not_null = False
    
    def __str__(self):
        return f"MAX({str(self.expr)})"
    
    def __eq__(self, other):
        if not isinstance(other, Max):
            return False
        return self.expr == other.expr
    
    def run(self, db, row, attrnames, sql):
        """
        Placeholder run method for aggregate context.
        
        Note: Actual aggregation will be handled by GroupBy.run() which will
        pass groups of rows instead of single rows. This method is here for
        interface compliance but shouldn't be called in normal aggregate usage.
        """
        raise NotImplementedError("Max.run should not be called directly; aggregation is handled in GroupBy.run()")
    
    def typecheck(self, dbt, tablet, sql):
        """
        Type check the MAX expression.
        
        MAX returns the same type as its input expression.
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
        Transform the MAX expression (for query transformation/optimization).
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            Transformed Max expression
        """
        # Transform the inner expression
        transformed_expr = self.expr.trans(dbt, tablet, sql)
        return Max(transformed_expr)
