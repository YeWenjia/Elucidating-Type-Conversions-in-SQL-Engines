"""
Aggregation functions module.

This module contains all SQL aggregate functions: COUNT, SUM, AVG, MAX, MIN.
"""

from interpreter.syntax.expression.aggregation.Count import Count
from interpreter.syntax.expression.aggregation.Sum import Sum
from interpreter.syntax.expression.aggregation.Avg import Avg
from interpreter.syntax.expression.aggregation.Max import Max
from interpreter.syntax.expression.aggregation.Min import Min

__all__ = ['Count', 'Sum', 'Avg', 'Max', 'Min', 'check_no_nested_aggregates']


def check_no_nested_aggregates(expr):
    """
    Check if an expression contains nested aggregate functions.
    Raises an error if nested aggregates are found.
    
    Args:
        expr: Expression to check
        
    Raises:
        Exception: If nested aggregates are detected
    """
    if expr is None:
        return
    
    # Import here to avoid circular dependency
    from interpreter.syntax.expression.Op import Op
    from interpreter.syntax.expression.And import And
    from interpreter.syntax.expression.Or import Or
    from interpreter.syntax.expression.BNeg import BNeg
    from interpreter.syntax.expression.Ascr import Ascr
    
    # Check if this expression is an aggregate
    if isinstance(expr, (Count, Sum, Avg, Max, Min)):
        raise Exception(f"Nested aggregate functions are not allowed: found {type(expr).__name__} inside another aggregate")
    
    # Recursively check subexpressions
    if isinstance(expr, Op):
        check_no_nested_aggregates(expr.e1)
        check_no_nested_aggregates(expr.e2)
    elif isinstance(expr, (And, Or)):
        check_no_nested_aggregates(expr.l)
        check_no_nested_aggregates(expr.r)
    elif isinstance(expr, BNeg):
        check_no_nested_aggregates(expr.b)
    elif isinstance(expr, Ascr):
        check_no_nested_aggregates(expr.e)
