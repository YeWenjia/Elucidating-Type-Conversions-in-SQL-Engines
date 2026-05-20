from interpreter.syntax.expression.Expression import Expr
from interpreter.syntax.expression.BValue import BValue, Natural, Real
from interpreter.syntax.type.ValueType import ZType, RType


class Sum(Expr):
    """
    Aggregate function: SUM(expr)
    Returns the sum of all values in the expression
    """
    
    def __init__(self, expr):
        """
        Initialize Sum aggregate function.
        
        Args:
            expr: Expression to sum (must be numeric)
        """
        super().__init__()
        # Check for nested aggregates
        from interpreter.syntax.expression.aggregation import check_no_nested_aggregates
        check_no_nested_aggregates(expr)
        self.expr = expr
        self.isnull = False
        self.isnull_not_null = False
    
    def __str__(self):
        return f"SUM({str(self.expr)})"
    
    def __eq__(self, other):
        if not isinstance(other, Sum):
            return False
        return self.expr == other.expr
    
    def run(self, db, row, attrnames, sql):
        """
        Placeholder run method for aggregate context.
        
        Note: Actual aggregation will be handled by GroupBy.run() which will
        pass groups of rows instead of single rows. This method is here for
        interface compliance but shouldn't be called in normal aggregate usage.
        """
        # For now, raise an error since this should be handled by GroupBy
        raise NotImplementedError("Sum.run should not be called directly; aggregation is handled in GroupBy.run()")
    
    def typecheck(self, dbt, tablet, sql):
        """
        Type check the SUM expression.
        
        SUM returns the same type as its input expression (must be numeric).
        For integers, SUM returns integer. For reals/decimals, SUM returns real.
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            The type of the input expression
        """
        # Type check the inner expression
        expr_type = self.expr.typecheck(dbt, tablet, sql)
        
        # Verify it's a numeric type
        if expr_type.tag not in ["Int", "Real"]:
            raise Exception(f"SUM requires numeric type, got {expr_type.tag}")
        
        # SUM returns the same type as its input
        return expr_type
    
    def trans(self, dbt, tablet, sql):
        """
        Transform the SUM expression (for query transformation/optimization).
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            Transformed Sum expression
        """
        # Transform the inner expression
        transformed_expr = self.expr.trans(dbt, tablet, sql)
        return Sum(transformed_expr)
