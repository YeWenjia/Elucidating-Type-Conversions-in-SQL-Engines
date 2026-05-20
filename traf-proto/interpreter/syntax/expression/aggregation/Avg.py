from interpreter.syntax.expression.Expression import Expr
from interpreter.syntax.expression.BValue import BValue, Real
from interpreter.syntax.type.ValueType import RType


class Avg(Expr):
    """
    Aggregate function: AVG(expr)
    Returns the average of all values in the expression
    """
    
    def __init__(self, expr):
        """
        Initialize Avg aggregate function.
        
        Args:
            expr: Expression to average (must be numeric)
        """
        super().__init__()
        # Check for nested aggregates
        from interpreter.syntax.expression.aggregation import check_no_nested_aggregates
        check_no_nested_aggregates(expr)
        self.expr = expr
        self.isnull = False
        self.isnull_not_null = False
    
    def __str__(self):
        return f"AVG({str(self.expr)})"
    
    def __eq__(self, other):
        if not isinstance(other, Avg):
            return False
        return self.expr == other.expr
    
    def run(self, db, row, attrnames, sql):
        """
        Placeholder run method for aggregate context.
        
        Note: Actual aggregation will be handled by GroupBy.run() which will
        pass groups of rows instead of single rows. This method is here for
        interface compliance but shouldn't be called in normal aggregate usage.
        """
        raise NotImplementedError("Avg.run should not be called directly; aggregation is handled in GroupBy.run()")
    
    def typecheck(self, dbt, tablet, sql):
        """
        Type check the AVG expression.
        
        AVG always returns a real/decimal type (RType), regardless of input type.
        The input expression must be numeric.
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            RType() - real/decimal type
        """
        # Type check the inner expression
        expr_type = self.expr.typecheck(dbt, tablet, sql)
        
        # Verify it's a numeric type
        if expr_type.tag not in ["Int", "Real"]:
            raise Exception(f"AVG requires numeric type, got {expr_type.tag}")
        
        # AVG always returns Real/Decimal type
        return RType()
    
    def trans(self, dbt, tablet, sql):
        """
        Transform the AVG expression (for query transformation/optimization).
        
        Args:
            dbt: Database type environment
            tablet: Table type (columns and their types)
            sql: SQL engine for type operations
            
        Returns:
            Transformed Avg expression
        """
        # Transform the inner expression
        transformed_expr = self.expr.trans(dbt, tablet, sql)
        return Avg(transformed_expr)
