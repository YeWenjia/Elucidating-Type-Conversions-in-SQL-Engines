"""
Alternative Lark-based SQL Parser (v2)

This parser uses Lark grammar to parse SQL and generates the same AST
as Parser.py (using Query, Proj, Sel, etc.) so it's compatible with
the existing typechecker and runtime.

Usage:
    from interpreter.lark_parser import LarkParser
    parser = LarkParser()
    ast = parser.parse("SELECT * FROM TA JOIN TB ON TA.name = TB.fullname")
"""

import datetime
from lark import Lark, Transformer, v_args, Token
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression.BValue import *
from interpreter.syntax.expression.Expression import *
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.Or import Or
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.expression.IsNull import IsNull
from interpreter.syntax.expression.NName import NName
from interpreter.syntax.expression.Op import Op, Lt, Eq, Like, Plus
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.Empty import Empty
from interpreter.syntax.expression.Ins import Ins
from interpreter.syntax.expression.ScalarSubquery import ScalarSubquery
from interpreter.syntax.expression.aggregation import Count, Sum, Avg, Max, Min
from interpreter.Parser import db  # Import table definitions


def is_aggregate_expr(expr):
    """Check if an expression is an aggregate function."""
    return isinstance(expr, (Count, Sum, Avg, Max, Min))


def expr_contains_aggregate(expr):
    """Recursively check if an expression contains an aggregate function."""
    if is_aggregate_expr(expr):
        return True
    if isinstance(expr, Alias):
        return expr_contains_aggregate(expr.e)
    if isinstance(expr, (Plus, Op)):
        # Check operands of binary operations
        if hasattr(expr, 'e1') and hasattr(expr, 'e2'):
            return expr_contains_aggregate(expr.e1) or expr_contains_aggregate(expr.e2)
    return False


# Comprehensive SQL grammar
sql_grammar = r"""
?start: query ";"?

// Query with set operations
?query: select_query
      | query "UNION"i query        -> union_query
      | query "INTERSECT"i query    -> intersect_query
      | query "EXCEPT"i query       -> except_query
      | query "MINUS"i query        -> minus_query

// SELECT statement
select_query: "SELECT"i distinct_flag? select_columns "FROM"i from_clause where_clause? group_by_clause? having_clause? order_by_clause? limit_clause?
            | "SELECT"i distinct_flag? select_columns

distinct_flag: "DISTINCT"i

// SELECT columns
select_columns: "*"                                -> wildcard
              | select_expr ("," select_expr)*    -> column_list

select_expr: expr ("AS"i identifier)?             -> aliased_expr

// FROM clause with JOINs
?from_clause: table_ref
           | from_clause "," table_ref            -> cross_join
           | from_clause "JOIN"i table_ref "ON"i condition          -> inner_join
           | from_clause "INNER"i "JOIN"i table_ref "ON"i condition -> inner_join
           | from_clause "JOIN"i table_ref                          -> cross_join
           | from_clause "CROSS"i "JOIN"i table_ref                 -> cross_join_explicit

?table_ref: identifier                             -> table_name
         | "(" query ")" ("AS"i)? identifier      -> subquery_alias
         | "(" query ")"                          -> subquery
         | identifier ("AS"i)? identifier         -> table_alias

// Identifier (can be quoted or unquoted)
identifier: CNAME | QUOTED_IDENTIFIER

// WHERE clause
where_clause: "WHERE"i condition

// GROUP BY clause
group_by_clause: "GROUP"i "BY"i expr ("," expr)*

// HAVING clause
having_clause: "HAVING"i condition

// ORDER BY clause
order_by_clause: "ORDER"i "BY"i order_spec ("," order_spec)*

order_spec: expr order_direction?

order_direction: "ASC"i   -> asc_direction
               | "DESC"i  -> desc_direction

// LIMIT clause
limit_clause: "LIMIT"i SIGNED_NUMBER offset_clause?

offset_clause: "OFFSET"i SIGNED_NUMBER

// Conditions (boolean expressions) — SQL precedence: NOT > AND > OR, all left-associative.
?condition: condition "OR"i and_term              -> or_cond
          | and_term
?and_term: and_term "AND"i not_term               -> and_cond
         | not_term
?not_term: "NOT"i not_term                        -> not_cond
         | comparison

?comparison: expr "=" expr                        -> eq
           | expr "<" expr                        -> lt
           | expr ">" expr                        -> gt
           | expr "<=" expr                       -> lte
           | expr ">=" expr                       -> gte
           | expr "!=" expr                       -> neq
           | expr "<>" expr                       -> neq
           | expr "LIKE"i expr                    -> like
           | expr "NOT"i "LIKE"i expr             -> not_like
           | expr "BETWEEN"i expr "AND"i expr     -> between
           | expr "NOT"i "BETWEEN"i expr "AND"i expr -> not_between
           | expr "IS"i "NULL"i                   -> is_null
           | expr "IS"i "NOT"i "NULL"i            -> is_not_null
           | tuple "IN"i "(" query ")"            -> in_query_tuple
           | expr "IN"i "(" query ")"             -> in_query
           | tuple "NOT"i "IN"i "(" query ")"     -> not_in_query_tuple
           | expr "NOT"i "IN"i "(" query ")"      -> not_in_query
           | "EXISTS"i "(" query ")"              -> exists_query
           | expr

// Tuple expression for multi-column IN
tuple: "(" expr ("," expr)+ ")"

// Expressions (with proper precedence)
?expr: expr "+" term                              -> add
     | expr "-" term                              -> sub
     | term

?term: term "*" factor                            -> mul
     | term "/" factor                            -> div
     | factor

?factor: aggregate_func
       | qualified_name
       | literal
       | "CAST"i "(" expr "AS"i type_name ")"     -> cast_expr
       | "(" condition ")"                        -> paren_condition
       | "(" query ")"                            -> subquery_expr
       | "(" expr ")"

qualified_name: identifier "." identifier         -> qualified_col
              | identifier                        -> simple_col

// Aggregate functions
aggregate_func: "COUNT"i "(" "*" ")"              -> count_star
              | "COUNT"i "(" "DISTINCT"i expr ")" -> count_distinct_expr
              | "COUNT"i "(" expr ")"             -> count_expr
              | "SUM"i "(" expr ")"               -> sum_expr
              | "AVG"i "(" expr ")"               -> avg_expr
              | "MAX"i "(" expr ")"               -> max_expr
              | "MIN"i "(" expr ")"               -> min_expr

// Type names for CAST (with optional parameters)
type_name: "INT"i                                           -> type_int
         | "INTEGER"i                                       -> type_integer
         | "FLOAT"i                                         -> type_float
         | "REAL"i                                          -> type_real
         | "DOUBLE"i                                        -> type_double
         | "TEXT"i                                          -> type_text
         | "STRING"i                                        -> type_string
         | "SIGNED"i                                        -> type_signed
         | "VARCHAR"i "(" SIGNED_NUMBER ")"                 -> type_varchar
         | "CHAR"i "(" SIGNED_NUMBER ")"                    -> type_char_len
         | "CHAR"i                                          -> type_char
         | "DECIMAL"i "(" SIGNED_NUMBER "," SIGNED_NUMBER ")" -> type_decimal
         | "DECIMAL"i                                       -> type_decimal_simple

// Literals
?literal: SIGNED_NUMBER                           -> number
        | SQL_STRING                              -> string
        | "NULL"i                                 -> null_value
        | "TRUE"i                                 -> true_value
        | "FALSE"i                                -> false_value
        | CURRENT_TIMESTAMP_KW                    -> current_timestamp
        | CURRENT_DATE_KW                         -> current_date
        | CURRENT_TIME_KW                         -> current_time
        | LOCALTIMESTAMP_KW                       -> current_timestamp
        | LOCALTIME_KW                            -> current_time

CURRENT_TIMESTAMP_KW.2: /CURRENT_TIMESTAMP/i
CURRENT_DATE_KW.2:      /CURRENT_DATE/i
CURRENT_TIME_KW.2:      /CURRENT_TIME/i
LOCALTIMESTAMP_KW.2:    /LOCALTIMESTAMP/i
LOCALTIME_KW.2:         /LOCALTIME/i

// Custom terminals
SQL_STRING: /'([^'\\]|\\.)*'/
QUOTED_IDENTIFIER: /"([^"\\]|\\.)*"/

%import common.CNAME
%import common.SIGNED_NUMBER  
%import common.WS
%ignore WS
"""

#TODO infer this somehow




class SQLToASTTransformer(Transformer):
    """Transform Lark parse tree to interpreter AST (Query objects)"""
    
    def __init__(self, schema, use_decimal=True):
        super().__init__()
        self.use_decimal = use_decimal
        self.schema = schema

    def project_children(self, children):
        left, right = children
        _left = left
        match left:
            case Proj():
                pass
            case _:
                aliascols1 = [Alias(NName(col), f'{col}') for col in left.get_col_names()]
                _left = Proj(Beta(aliascols1), left)
        _right = right
        match right:
            case Proj():
                pass
            case _:
                aliascols2 = [Alias(NName(col), f'{col}') for col in right.get_col_names()]
                _right = Proj(Beta(aliascols2), right)
    
        return (_left, _right)
    
    # Query operations
    def union_query(self, children):
        left, right = self.project_children(children)
        return Setop("∪", left, right)
    
    def intersect_query(self, children):
        left, right = self.project_children(children)
        return Setop("∩", left, right)
    
    def except_query(self, children):
        left, right = self.project_children(children)
        return Setop("-", left, right)
    
    def minus_query(self, children):
        left, right = self.project_children(children)
        return Setop("-", left, right)
    
    # SELECT statement
    def select_query(self, children):
        """Handle SELECT with various clauses passed as a list"""
        # children is a list of all matched elements from the grammar rule
        # select_query: "SELECT"i distinct_flag? select_columns "FROM"i from_clause where_clause? group_by_clause? having_clause? order_by_clause? limit_clause?
        # So children = [distinct_flag?, select_columns, from_clause, where?, group_by?, having?, order_by?, limit?]
        
        if len(children) == 0:
            return Rel("dual", [])
        
        # Check if first child is from distinct_flag rule
        first_child = children[0]
        has_distinct = False
        offset = 0
        
        # If first child is a string "DISTINCT", it came from distinct_flag rule
        if isinstance(first_child, str) and first_child.upper() == 'DISTINCT':
            has_distinct = True
            offset = 1
        
        select_cols = children[offset]
        
        # Check if we have a FROM clause
        if len(children) < offset + 2:
            # SELECT without FROM (e.g., SELECT 1+1)
            if isinstance(select_cols, str) and select_cols == '*':
                return Rel("dual", [])
            elif isinstance(select_cols, list):
                return Proj(Beta(select_cols), Rel("dual", []))
            return Rel("dual", [])
        
        from_query = children[offset + 1]
        where_cond = None
        group_by_exprs = None
        having_cond = None
        order_by_specs = None
        limit_info = None
        
        # Parse remaining clauses
        for idx in range(offset + 2, len(children)):
            arg = children[idx]
            if isinstance(arg, tuple) and arg[0] == 'WHERE':
                where_cond = arg[1]
            elif isinstance(arg, tuple) and arg[0] == 'GROUP BY':
                group_by_exprs = arg[1]
            elif isinstance(arg, tuple) and arg[0] == 'HAVING':
                having_cond = arg[1]
            elif isinstance(arg, tuple) and arg[0] == 'ORDER BY':
                order_by_specs = arg[1]
            elif isinstance(arg, tuple) and arg[0] == 'LIMIT':
                limit_info = arg[1]
        
        # Build query from bottom up: FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT
        # Auto-qualify a bare Rel source so its columns enter outer scope as
        # TABLE.col. Without this, a correlated subquery can shadow the outer
        # table's unqualified columns and make references like EMP.ENAME
        # unresolvable. JOIN sources already go through _auto_qualify.
        query = self._auto_qualify(from_query)
        
        # Apply WHERE
        if where_cond is not None:
            query = Sel(where_cond, query)
        
        # Apply GROUP BY (with HAVING if present)
        # Special handling: if ORDER BY contains aggregates not in SELECT, add them first
        added_order_aggregates = []  # Track aggregates we add for ORDER BY
        modified_order_specs = None  # Modified ORDER BY specs with column refs instead of aggregates
        
        if group_by_exprs is not None:
            # For GROUP BY, we need the SELECT columns
            if isinstance(select_cols, str) and select_cols == '*':
                # SELECT * with GROUP BY is usually an error, but handle it
                working_select_cols = []
            else:
                working_select_cols = list(select_cols)
            
            # Check if ORDER BY has aggregate expressions not in SELECT
            if order_by_specs is not None:
                # Extract expressions in SELECT (including aggregates)
                select_exprs = []
                select_expr_to_name = {}  # Map expression to its column name
                for col_expr in working_select_cols:
                    if isinstance(col_expr, Alias):
                        select_exprs.append(col_expr.e)
                        select_expr_to_name[str(col_expr.e)] = col_expr.name
                    else:
                        select_exprs.append(col_expr)
                
                # Build new ORDER BY specs, replacing aggregates with column references
                modified_order_specs = []
                for idx, (order_expr, direction) in enumerate(order_by_specs):
                    # Check if it's an aggregate
                    if expr_contains_aggregate(order_expr):
                        # Check if this aggregate is already in SELECT
                        existing_col_name = None
                        for select_expr in select_exprs:
                            # Safe comparison: check type and str representation
                            try:
                                if type(select_expr) == type(order_expr) and str(select_expr) == str(order_expr):
                                    # Found it - get its column name
                                    existing_col_name = select_expr_to_name.get(str(select_expr))
                                    break
                            except:
                                # If comparison fails, assume they're different
                                pass
                        
                        if existing_col_name:
                            # Aggregate is already in SELECT, use its column name
                            modified_order_specs.append((NName(existing_col_name), direction))
                        else:
                            # Not in SELECT, add it with a generated name
                            gen_name = f"__order_agg_{idx}"
                            working_select_cols.append(Alias(order_expr, gen_name))
                            added_order_aggregates.append(gen_name)
                            # Replace aggregate with column reference in ORDER BY
                            modified_order_specs.append((NName(gen_name), direction))
                    else:
                        # Not an aggregate - check if it's already in SELECT
                        order_name = str(order_expr) if isinstance(order_expr, NName) else None
                        if order_name and order_name in [a.name for a in working_select_cols if isinstance(a, Alias)]:
                            # Already in SELECT, keep as-is
                            modified_order_specs.append((order_expr, direction))
                        elif order_name:
                            # Column not in SELECT, add it temporarily
                            gen_name = f"__order_col_{idx}"
                            working_select_cols.append(Alias(order_expr, gen_name))
                            added_order_aggregates.append(gen_name)
                            modified_order_specs.append((NName(gen_name), direction))
                        else:
                            modified_order_specs.append((order_expr, direction))
            
            # Create GROUP BY with potentially expanded select_cols
            query = GroupBy(Beta(working_select_cols), group_by_exprs, query, having_cond)
        elif having_cond is not None:
            # HAVING without GROUP BY - treat as WHERE (non-standard but handle it)
            query = Sel(having_cond, query)
        # Apply SELECT projection
        if isinstance(select_cols, str) and select_cols == '*':
            # SELECT * - no projection wrapper
            final_query = query
            final_select_cols = None
        elif group_by_exprs is not None:
            # GROUP BY already has the projection in Beta
            # No additional projection needed here
            final_query = query
            # If we added aggregates for ORDER BY, we'll need to project them out later
            if added_order_aggregates:
                # Use column references to already-computed aliases, not the original expressions
                final_select_cols = []
                for col_expr in select_cols:
                    if isinstance(col_expr, Alias):
                        final_select_cols.append(Alias(NName(col_expr.name), col_expr.name))
                    else:
                        final_select_cols.append(col_expr)
            else:
                final_select_cols = None
        else:
            # No explicit GROUP BY — check if SELECT contains aggregates (implicit GROUP BY)
            has_select_aggregates = isinstance(select_cols, list) and any(
                expr_contains_aggregate(col) for col in select_cols
            )
            if has_select_aggregates:
                # Implicit GROUP BY: aggregate in SELECT without GROUP BY
                # Also handle ORDER BY aggregates like the explicit GROUP BY path
                working_select_cols = list(select_cols)
                if order_by_specs is not None:
                    select_exprs = []
                    select_expr_to_name = {}
                    for col_expr in working_select_cols:
                        if isinstance(col_expr, Alias):
                            select_exprs.append(col_expr.e)
                            select_expr_to_name[str(col_expr.e)] = col_expr.name
                        else:
                            select_exprs.append(col_expr)

                    modified_order_specs = []
                    for idx, (order_expr, direction) in enumerate(order_by_specs):
                        if expr_contains_aggregate(order_expr):
                            existing_col_name = None
                            for select_expr in select_exprs:
                                try:
                                    if type(select_expr) == type(order_expr) and str(select_expr) == str(order_expr):
                                        existing_col_name = select_expr_to_name.get(str(select_expr))
                                        break
                                except:
                                    pass
                            if existing_col_name:
                                modified_order_specs.append((NName(existing_col_name), direction))
                            else:
                                gen_name = f"__order_agg_{idx}"
                                working_select_cols.append(Alias(order_expr, gen_name))
                                added_order_aggregates.append(gen_name)
                                modified_order_specs.append((NName(gen_name), direction))
                        else:
                            modified_order_specs.append((order_expr, direction))

                query = GroupBy(Beta(working_select_cols), [], query, having_cond)
                final_query = query
                if added_order_aggregates:
                    final_select_cols = []
                    for col_expr in select_cols:
                        if isinstance(col_expr, Alias):
                            final_select_cols.append(Alias(NName(col_expr.name), col_expr.name))
                        else:
                            final_select_cols.append(col_expr)
                else:
                    final_select_cols = None
            # Normal SELECT with projection (no GROUP BY, no aggregates)
            # Check if ORDER BY references columns not in SELECT
            elif order_by_specs is not None:
                # Extract column names referenced in ORDER BY
                order_by_cols = set()
                for expr, direction in order_by_specs:
                    if isinstance(expr, NName):
                        order_by_cols.add(expr.name)
                
                # Extract column names in SELECT
                select_col_names = set()
                for col_expr in select_cols:
                    if isinstance(col_expr, Alias):
                        if isinstance(col_expr.e, NName):
                            select_col_names.add(col_expr.e.name)
                    elif isinstance(col_expr, NName):
                        select_col_names.add(col_expr.name)
                
                # Find columns in ORDER BY but not in SELECT
                missing_cols = order_by_cols - select_col_names
                
                if missing_cols:
                    # Need to include missing columns temporarily
                    # Create a projection with SELECT columns + missing ORDER BY columns
                    temp_cols = list(select_cols)  # Original SELECT columns
                    for col_name in missing_cols:
                        temp_cols.append(Alias(NName(col_name), col_name))
                    
                    # Create temporary projection with all needed columns
                    temp_query = Proj(Beta(temp_cols), query)
                    
                    # Store the original select_cols for final projection
                    final_select_cols = select_cols
                    final_query = temp_query
                else:
                    # All ORDER BY columns are in SELECT, proceed normally
                    final_query = Proj(Beta(select_cols), query)
                    final_select_cols = None
            else:
                # No ORDER BY, proceed normally
                final_query = Proj(Beta(select_cols), query)
                final_select_cols = None
        
        # Wrap in Eps if DISTINCT
        if has_distinct:
            final_query = Eps(final_query)
        
        # Apply ORDER BY
        if order_by_specs is not None:
            # Use modified specs if we had to replace aggregates with column refs
            actual_order_specs = modified_order_specs if modified_order_specs is not None else order_by_specs
            final_query = OrderBy(final_query, actual_order_specs)
            
            # If we added extra columns for ORDER BY, project them out now
            if 'final_select_cols' in locals() and final_select_cols is not None:
                final_query = Proj(Beta(final_select_cols), final_query)
        
        # Apply LIMIT
        if limit_info is not None:
            limit_count, offset_val = limit_info
            final_query = Limit(final_query, limit_count, offset_val)
        
        return final_query
    
    def wildcard(self, *args):
        return '*'
    
    def distinct_flag(self, children):
        """Mark that DISTINCT was present"""
        return 'DISTINCT'
    
    def column_list(self, children):
        return list(children)
    
    def aliased_expr(self, children):
        if len(children) == 2:
            expr, alias = children
            return Alias(expr, str(alias))
        else:
            expr = children[0]
            # Auto-alias: use expression string as alias name
            if isinstance(expr, NName):
                return Alias(expr, expr.name)
            elif isinstance(expr, (Count, Sum, Avg, Max, Min)):
                return Alias(expr, str(expr))
            else:
                return Alias(expr, str(expr))
    
    # FROM clause
    def table_name(self, children):
        name = children[0]
        table_name = str(name)
        # Try schema first, then fall back to global db
        if table_name in self.schema:
            return Rel(table_name, self.schema[table_name].getColNames())
        elif table_name in db:
            return Rel(table_name, db[table_name].cols)
        return Rel(table_name, [])
    
    def subquery(self, children):
        return children[0]
    
    # SQL keywords that must not be accepted as table/subquery aliases. Without
    # this check, queries like `EMP FULL JOIN t0 ON ...` would parse as "table
    # EMP aliased FULL" followed by an inner join, silently losing the outer-
    # join semantics instead of failing fast.
    _RESERVED_ALIAS_KEYWORDS = frozenset({
        "LEFT", "RIGHT", "FULL", "OUTER", "INNER", "CROSS", "NATURAL",
    })

    def _reject_reserved_alias(self, alias):
        if str(alias).upper() in self._RESERVED_ALIAS_KEYWORDS:
            raise ValueError(
                f"reserved SQL keyword '{alias}' cannot be used as a table alias"
            )

    def subquery_alias(self, children):
        # children = [query, alias_name]
        subquery, alias = children
        self._reject_reserved_alias(alias)
        # Strip any existing table prefix before applying the new alias, so
        # `(SELECT * FROM DEPT) AS t3` yields `t3.DEPTNO`/`t3.NAME` instead of
        # `t3.DEPT.DEPTNO`/`t3.DEPT.NAME` once the inner Rel has been
        # auto-qualified upstream.
        def _base(col):
            return col.rsplit('.', 1)[-1] if '.' in col else col
        aliascols = [Alias(NName(col), f'{alias}.{_base(col)}') for col in subquery.get_col_names()]
        return Proj(Beta(aliascols), subquery)

    def table_alias(self, children):
        if len(children) == 2:
            # table_name AS alias
            tablename, alias = children
            self._reject_reserved_alias(alias)
            # Get column names from schema or db
            if tablename in self.schema:
                col_names = self.schema[tablename].getColNames()
            elif tablename in db:
                col_names = db[tablename].cols
            else:
                # If not found, return an empty Rel - this will be caught later
                col_names = []
            
            table = Rel(tablename, col_names)
            # Note: table is already a Query object from table_name rule
            if isinstance(table, Rel):
                alias_cols = [Alias(NName(col), f'{alias}.{col}') for col in table.get_col_names()]
                return Proj(Beta(alias_cols), table)
            return table
        else:
            # Just table name
            return children[0]
    
    def _auto_qualify(self, node):
        """If node is a bare Rel (no alias), qualify columns with table name."""
        if isinstance(node, Rel):
            alias_cols = [Alias(NName(col), f'{node.tablename}.{col}') for col in node.get_col_names()]
            return Proj(Beta(alias_cols), node)
        return node

    def cross_join(self, children):
        left, right = children
        return Setop("X", self._auto_qualify(left), self._auto_qualify(right))

    def cross_join_explicit(self, children):
        left, right = children
        return Setop("X", self._auto_qualify(left), self._auto_qualify(right))

    def inner_join(self, children):
        left, right, condition = children
        cross_product = Setop("X", self._auto_qualify(left), self._auto_qualify(right))
        return Sel(condition, cross_product)
    
    # WHERE/HAVING
    def where_clause(self, children):
        return ('WHERE', children[0])
    
    def having_clause(self, children):
        return ('HAVING', children[0])
    
    # GROUP BY
    def group_by_clause(self, children):
        return ('GROUP BY', list(children))
    
    # ORDER BY
    def order_by_clause(self, children):
        """Returns ('ORDER BY', list of (expr, direction) tuples)"""
        return ('ORDER BY', list(children))
    
    def order_spec(self, children):
        """Returns (expression, direction) tuple"""
        if len(children) == 2:
            expr, direction = children
            return (expr, direction)
        else:
            # No direction specified, default to ASC
            expr = children[0]
            return (expr, 'ASC')
    
    def asc_direction(self, children):
        """Returns 'ASC' string"""
        return 'ASC'
    
    def desc_direction(self, children):
        """Returns 'DESC' string"""
        return 'DESC'
    
    # LIMIT and OFFSET
    def limit_clause(self, children):
        """Returns ('LIMIT', (limit_count, offset)) tuple"""
        limit_count = int(children[0])
        offset = int(children[1]) if len(children) > 1 else 0
        return ('LIMIT', (limit_count, offset))
    
    def offset_clause(self, children):
        """Returns the offset value as int"""
        return int(children[0])
    
    # Conditions
    def and_cond(self, children):
        left, right = children
        return And(left, right)
    
    def or_cond(self, children):
        left, right = children
        return Or(left, right)
    
    def not_cond(self, children):
        return BNeg(children[0])
    
    def eq(self, children):
        left, right = children
        # Wrap Query operands in ScalarSubquery for comparisons
        if isinstance(right, Query):
            right = ScalarSubquery(right)
        if isinstance(left, Query):
            left = ScalarSubquery(left)
        return Eq(left, right)
    
    def lt(self, children):
        left, right = children
        # Wrap Query operands in ScalarSubquery for comparisons
        if isinstance(right, Query):
            right = ScalarSubquery(right)
        if isinstance(left, Query):
            left = ScalarSubquery(left)
        return Lt(left, right)
    
    def gt(self, children):
        left, right = children
        # Wrap Query operands in ScalarSubquery for comparisons
        if isinstance(right, Query):
            right = ScalarSubquery(right)
        if isinstance(left, Query):
            left = ScalarSubquery(left)
        return Lt(right, left)  # a > b is b < a
    
    def lte(self, children):
        left, right = children
        # Wrap Query operands in ScalarSubquery for comparisons
        if isinstance(right, Query):
            right = ScalarSubquery(right)
        if isinstance(left, Query):
            left = ScalarSubquery(left)
        # a <= b is NOT(b < a)
        return BNeg(Lt(right, left))
    
    def gte(self, children):
        left, right = children
        # Wrap Query operands in ScalarSubquery for comparisons
        if isinstance(right, Query):
            right = ScalarSubquery(right)
        if isinstance(left, Query):
            left = ScalarSubquery(left)
        # a >= b is NOT(a < b)
        return BNeg(Lt(left, right))
    
    def neq(self, children):
        left, right = children
        # Wrap Query operands in ScalarSubquery for comparisons
        if isinstance(right, Query):
            right = ScalarSubquery(right)
        if isinstance(left, Query):
            left = ScalarSubquery(left)
        # a != b is NOT(a = b)
        return BNeg(Eq(left, right))
    
    def like(self, children):
        left, right = children
        return Like(left, right)

    def not_like(self, children):
        left, right = children
        return BNeg(Like(left, right))

    def between(self, children):
        """Transform BETWEEN to >= AND <=
        expr BETWEEN low AND high => expr >= low AND expr <= high
        """
        expr, low, high = children
        # Wrap Query operands in ScalarSubquery if needed
        if isinstance(low, Query):
            low = ScalarSubquery(low)
        if isinstance(high, Query):
            high = ScalarSubquery(high)
        # expr >= low is NOT(expr < low)
        gte_cond = BNeg(Lt(expr, low))
        # expr <= high is NOT(high < expr)
        lte_cond = BNeg(Lt(high, expr))
        return And(gte_cond, lte_cond)
    
    def not_between(self, children):
        """Transform NOT BETWEEN to < OR >
        expr NOT BETWEEN low AND high => expr < low OR expr > high
        """
        expr, low, high = children
        # Wrap Query operands in ScalarSubquery if needed
        if isinstance(low, Query):
            low = ScalarSubquery(low)
        if isinstance(high, Query):
            high = ScalarSubquery(high)
        # expr < low
        lt_cond = Lt(expr, low)
        # expr > high is high < expr
        gt_cond = Lt(high, expr)
        return Or(lt_cond, gt_cond)
    
    def is_null(self, children):
        return IsNull(children[0])
    
    def is_not_null(self, children):
        return BNeg(IsNull(children[0]))
    
    def tuple(self, children):
        """Handle tuple expressions like (expr1, expr2, ...)"""
        return list(children)
    
    def in_query(self, children):
        expr, query = children
        return Ins([expr], query)
    
    def in_query_tuple(self, children):
        """Handle tuple IN query like (expr1, expr2) IN (SELECT ...)"""
        tuple_exprs, query = children
        return Ins(tuple_exprs, query)
    
    def not_in_query(self, children):
        """Handle NOT IN query like expr NOT IN (SELECT ...)"""
        expr, query = children
        return BNeg(Ins([expr], query))
    
    def not_in_query_tuple(self, children):
        """Handle tuple NOT IN query like (expr1, expr2) NOT IN (SELECT ...)"""
        tuple_exprs, query = children
        return BNeg(Ins(tuple_exprs, query))
    
    def exists_query(self, children):
        return Empty(children[0])
    
    # Expressions
    def add(self, children):
        left, right = children
        return Plus(left, right)
    
    def sub(self, children):
        left, right = children
        return Op("-", left, right)
    
    def mul(self, children):
        left, right = children
        return Op("*", left, right)
    
    def div(self, children):
        left, right = children
        return Op("/", left, right)
    
    def qualified_col(self, children):
        table, col = children
        return NName(f"{table}.{col}")
    
    def simple_col(self, children):
        return NName(str(children[0]))
    
    def identifier(self, children):
        """Handle both quoted and unquoted identifiers"""
        token = children[0]
        identifier_str = str(token)
        
        # If it's a QUOTED_IDENTIFIER, strip the quotes
        if token.type == 'QUOTED_IDENTIFIER':
            # Remove the surrounding double quotes
            identifier_str = identifier_str[1:-1]
            # Unescape any escaped quotes
            identifier_str = identifier_str.replace('\\\"', '"')
            identifier_str = identifier_str.replace('\\\\', '\\')
        
        return identifier_str
    
    def cast_expr(self, children):
        expr, type_str = children
        if type_str in ('INT', 'INTEGER', 'SIGNED'):
            return Ascr(expr, ZType())
        elif type_str in ('FLOAT', 'REAL', 'DOUBLE', 'DECIMAL'):
            return Ascr(expr, RType())
        elif type_str in ('TEXT', 'VARCHAR', 'CHAR', 'STRING'):
            return Ascr(expr, SType())
        else:
            return Ascr(expr, ZType())  # Default to int
    
    def paren_condition(self, children):
        """Handle boolean conditions in parentheses used as expressions"""
        return children[0]
    
    def subquery_expr(self, children):
        """Wrap a (SELECT ...) used in an expression position as a scalar subquery."""
        return ScalarSubquery(children[0])
    
    # Aggregates
    def count_star(self, children):
        return Count(None)
    
    def count_distinct_expr(self, children):
        return Count(children[0], distinct=True)
    
    def count_expr(self, children):
        return Count(children[0])
    
    def sum_expr(self, children):
        return Sum(children[0])
    
    def avg_expr(self, children):
        return Avg(children[0])
    
    def max_expr(self, children):
        return Max(children[0])
    
    def min_expr(self, children):
        return Min(children[0])
    
    # Literals
    def number(self, children):
        n = children[0]
        val = float(n) if '.' in str(n) else int(n)
        if isinstance(val, int):
            return Natural(val)
        else:
            return Real(val, self.use_decimal)
    
    def string(self, children):
        s = children[0]
        # Remove quotes
        return SString(str(s)[1:-1])
    
    def null_value(self, children):
        return Nullv(None)
    
    def true_value(self, children):
        return Boolean(True)
    
    def false_value(self, children):
        return Boolean(False)

    def current_timestamp(self, children):
        return DateTime(datetime.datetime.now())

    def current_date(self, children):
        return DateTime(datetime.date.today())

    def current_time(self, children):
        return DateTime(datetime.datetime.now().time())
    
    # Type name transformers
    def type_int(self, children):
        return "INT"
    
    def type_integer(self, children):
        return "INTEGER"
    
    def type_float(self, children):
        return "FLOAT"
    
    def type_real(self, children):
        return "REAL"
    
    def type_double(self, children):
        return "DOUBLE"
    
    def type_text(self, children):
        return "TEXT"
    
    def type_string(self, children):
        return "STRING"
    
    def type_signed(self, children):
        return "SIGNED"
    
    def type_varchar(self, children):
        # children contains the VARCHAR length, but we ignore it for type checking
        return "VARCHAR"
    
    def type_char(self, children):
        return "CHAR"
    
    def type_char_len(self, children):
        # children contains the CHAR length, but we ignore it for type checking
        return "CHAR"
    
    def type_decimal(self, children):
        # children contains precision and scale, but we ignore them for type checking
        return "DECIMAL"
    
    def type_decimal_simple(self, children):
        return "DECIMAL"


class LarkParser:
    """Lark-based SQL parser that generates the same AST as Parser.py"""
    
    def __init__(self, use_decimal=True, schema=None):
        self.use_decimal = use_decimal
        self.schema = schema or {
            "TA": RelationType([NameType("name", SType()), NameType("height", RType()), NameType("age", ZType())]),
            "TB": RelationType(
                [NameType("realage", ZType()), NameType("fullname", SType()), NameType("fullheight", RType())]),
            "TC": RelationType(
                [NameType("newage", ZType()), NameType("newheight", RType()), NameType("newname", SType())])
        }
        self.transformer = SQLToASTTransformer(self.schema, use_decimal)
        self.parser = Lark(sql_grammar, parser="lalr", start="start")
        
    
    def parse(self, sql_query: str) -> Query:
        """Parse SQL query and return Query AST"""
        try:
            tree = self.parser.parse(sql_query)
            ast = self.transformer.transform(tree)
            return ast
        except Exception as e:
            raise Exception(f"Lark parsing failed: {e}")


# Example usage and testing
if __name__ == "__main__":
    parser = LarkParser()
    
    # Test queries
    queries = [
        "SELECT * FROM TA",
        "SELECT name, age FROM TA WHERE age > 25",
        "SELECT TA.name, TB.realage FROM TA JOIN TB ON TA.name = TB.fullname",
        "SELECT name, COUNT(*) AS cnt FROM TA GROUP BY name",
        "SELECT * FROM TA WHERE age > 25 AND name = 'Alice'",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            ast = parser.parse(query)
            print(f"AST: {ast}")
        except Exception as e:
            print(f"Error: {e}")
