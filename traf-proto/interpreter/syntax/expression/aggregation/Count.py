from interpreter.syntax.expression.Expression import Expr
from interpreter.syntax.expression.BValue import BValue, Natural
from interpreter.syntax.type.ValueType import ZType


class Count(Expr):
    """
    Aggregate function: COUNT(*) or COUNT(expr)
    Returns the number of rows (or non-NULL values if expr is specified)
    """
    
    def __init__(self, expr=None, distinct=False):
        """
        Initialize Count aggregate function.
        
        Args:
            expr: Expression to count, or None/"*" for COUNT(*)
            distinct: Boolean flag for COUNT(DISTINCT expr)
        """
        super().__init__()
        # Check for nested aggregates
        from interpreter.syntax.expression.aggregation import check_no_nested_aggregates
        check_no_nested_aggregates(expr)
        self.expr = expr
        self.distinct = distinct
        self.isnull = False
        self.isnull_not_null = False
    
    def __str__(self):
        if self.expr is None or (isinstance(self.expr, str) and self.expr == "*"):
            return "COUNT(*)"
        elif self.distinct:
            return f"COUNT(DISTINCT {str(self.expr)})"
        else:
            return f"COUNT({str(self.expr)})"
    
    def __eq__(self, other):
        if not isinstance(other, Count):
            return False
        return self.expr == other.expr and self.distinct == other.distinct
    
    def run(self, db, row, attrnames, sql):
        """
        Placeholder run method for aggregate context.
        
        Note: Actual aggregation will be handled by GroupBy.run() which will
        pass groups of rows instead of single rows. This method is here for
        interface compliance but shouldn't be called in normal aggregate usage.
        """
        # For now, return a placeholder
        # This will be properly implemented when GroupBy handles aggregates
        raise NotImplementedError("Count.run should not be called directly; aggregation is handled in GroupBy.run()")
    
    def typecheck(self, dbt, tablet, sql):
        """
        Type check the COUNT expression.
        
        COUNT always returns an integer (ZType), regardless of input type.
        If expr is specified, we need to verify it type checks properly.
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            ZType() - integer type
        """
        if self.expr is not None and not (isinstance(self.expr, str) and self.expr == "*"):
            # Type check the inner expression to ensure it's valid
            # We don't care about the result type, just that it's valid
            self.expr.typecheck(dbt, tablet, sql)
        
        # COUNT always returns integer
        return ZType()
    
    def trans(self, dbt, tablet, sql):
        """
        Transform the COUNT expression (for query transformation/optimization).
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            Transformed Count expression
        """
        if self.expr is not None and not (isinstance(self.expr, str) and self.expr == "*"):
            # Transform the inner expression
            transformed_expr = self.expr.trans(dbt, tablet, sql)
            return Count(transformed_expr, distinct=self.distinct)
        else:
            # COUNT(*) has no inner expression to transform
            return Count(self.expr, distinct=self.distinct)
