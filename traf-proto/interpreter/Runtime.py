from interpreter.AbstractOps import AbstractOps
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression import Expression
from interpreter.syntax.expression.IsNull import IsNull
from interpreter.syntax.expression.NName import NName
from interpreter.syntax.expression.Op import Op
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.expression.BValue import *
from interpreter.syntax.type.RelationType import *
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.Or import Or
from interpreter.syntax.expression.Empty import Empty
from interpreter.syntax.expression.Ins import Ins
from interpreter.syntax.expression.ScalarSubquery import ScalarSubquery
from interpreter.syntax.expression.aggregation import Count, Sum, Avg, Max, Min
from interpreter.syntax.type.Database import Database


class _ReverseKey:
    """Wrapper to reverse comparison order for DESC sorting of non-numeric types."""
    __slots__ = ('value',)
    def __init__(self, value):
        self.value = value
    def __lt__(self, other):
        return self.value > other.value
    def __le__(self, other):
        return self.value >= other.value
    def __gt__(self, other):
        return self.value < other.value
    def __ge__(self, other):
        return self.value <= other.value
    def __eq__(self, other):
        return self.value == other.value


class Eta:
    """
    Environment for runtime value lookup. Maps column names to values.
    Supports qualified and unqualified name resolution.
    """
    
    def __init__(self, row, cols):
        """
        Create an Eta environment from a row of values and column names.
        
        Args:
            row: List of BValue objects (the row values)
            cols: List of column name strings
        """
        self.row = row
        self.cols = cols
    
    def find_column_index(self, name):
        """
        Find the index of a column by name, handling both qualified and unqualified lookups.
        Mirrors the logic in Runtime.find_column_index().
        """
        attrnames = self.cols
        
        # Try exact match first
        if name in attrnames:
            return attrnames.index(name)
        
        # If the lookup name is qualified (contains a dot), try stripping the table prefix
        if '.' in name:
            unqualified_name = name.split('.', 1)[1]  # Get the part after the first dot
            if unqualified_name in attrnames:
                return attrnames.index(unqualified_name)
        
        # If the lookup name is unqualified, try matching against qualified columns
        elif '.' not in name:
            matches = []
            for i, attrname in enumerate(attrnames):
                if '.' in attrname:
                    # Extract the column name part (after the dot)
                    col_name = attrname.split('.', 1)[1]
                    if col_name == name:
                        matches.append(i)
                # Also check if the full name matches (for non-qualified columns)
                elif attrname == name:
                    matches.append(i)
            
            # If we found exactly one match, return it
            if len(matches) == 1:
                return matches[0]
            # If multiple matches, return the last one (innermost scope)
            elif len(matches) > 1:
                return matches[-1]
        
        # Not found - raise the standard error
        raise ValueError(f"'{name}' is not in list")
    
    def get(self, name):
        """
        Get the value for a column by name.
        
        Args:
            name: Column name (qualified or unqualified)
            
        Returns:
            BValue for the column
        """
        idx = self.find_column_index(name)
        return self.row[idx]
    
    def merge(self, other):
        """
        Merge this Eta with another Eta, with 'other' taking precedence.
        Qualified names shadow their unqualified counterparts.
        
        Args:
            other: Another Eta to merge with
            
        Returns:
            New Eta with merged columns and values
        """
        # Create merged column dict
        col_dict = {}

        #print("[DEBUG] Mergin ", self, " with ", other)
        #print("[DEBUG] other cols: ", other.cols, " other row: ", other.row)
        
        # Add columns from self
        for i, col in enumerate(self.cols):
            col_dict[col] = self.row[i]
        
        # Add/replace with columns from other, handling shadowing
        for i, col in enumerate(other.cols):
            col_dict[col] = other.row[i]
            
            # If this is a qualified column (e.g., 'N1.stuid'), shadow the unqualified version
            if '.' in col:
                unqualified = col.split('.', 1)[1]  # Get part after first dot
                # Remove the unqualified version if it exists
                if unqualified in col_dict:
                    del col_dict[unqualified]
        
        # Convert back to lists maintaining order
        merged_cols = list(col_dict.keys())
        merged_row = [col_dict[col] for col in merged_cols]
        
        return Eta(merged_row, merged_cols)
    
    def __str__(self):
        return f"Eta({{ {', '.join(f'{col}: {val}' for col, val in zip(self.cols, self.row))} }})"


class Runtime:
    # ops: AbstractOps

    def __init__(self, ops):
        self.ops = ops

    def find_column_index(self, name, attrnames):
        """
        Find the index of a column by name, handling both qualified and unqualified lookups.
        
        This mirrors the logic in RelationType.getTypeByName():
        - First try exact match
        - If name is qualified (has '.'), try stripping table prefix
        - If name is unqualified, try matching against qualified columns
        """
        # Try exact match first
        if name in attrnames:
            return attrnames.index(name)
        
        # If the lookup name is qualified (contains a dot), try stripping the table prefix
        if '.' in name:
            unqualified_name = name.split('.', 1)[1]  # Get the part after the first dot
            if unqualified_name in attrnames:
                return attrnames.index(unqualified_name)
        
        # If the lookup name is unqualified, try matching against qualified columns
        elif '.' not in name:
            matches = []
            for i, attrname in enumerate(attrnames):
                if '.' in attrname:
                    # Extract the column name part (after the dot)
                    col_name = attrname.split('.', 1)[1]
                    if col_name == name:
                        matches.append(i)
                # Also check if the full name matches (for non-qualified columns)
                elif attrname == name:
                    matches.append(i)
            
            # If we found exactly one match, return it
            if len(matches) == 1:
                return matches[0]
            # If multiple matches, return the first one
            # (SQL would normally raise an ambiguous column error)
            elif len(matches) > 1:
                return matches[0]
        
        # Not found - raise the standard error
        raise ValueError(f"'{name}' is not in list")

    def has_aggregates(self, expr):
        """Check if an expression contains aggregate functions."""
        if isinstance(expr, (Count, Sum, Avg, Max, Min)):
            return True
        # Check nested expressions
        if hasattr(expr, 'e1') and self.has_aggregates(expr.e1):
            return True
        if hasattr(expr, 'e2') and self.has_aggregates(expr.e2):
            return True
        if hasattr(expr, 'l') and self.has_aggregates(expr.l):
            return True
        if hasattr(expr, 'r') and self.has_aggregates(expr.r):
            return True
        if hasattr(expr, 'e') and self.has_aggregates(expr.e):
            return True
        if hasattr(expr, 'b') and self.has_aggregates(expr.b):
            return True
        return False

    def eval_aggregate(self, db, agg_expr, table: Table, eta: Eta):
        """Evaluate an aggregate function on a group of rows."""
        if isinstance(agg_expr, Count):
            if agg_expr.expr is None:
                # COUNT(*) - count all rows
                return Natural(len(table.rows))
            elif agg_expr.distinct:
                # COUNT(DISTINCT expr) - count distinct non-NULL values
                print("[DEBUG] Evaluating COUNT(*) on table with ", table)
                seen = set()
                for row in table.rows:
                    row_eta = eta.merge(Eta(row, table.cols))
                    val = self.run_expr(db, row_eta, agg_expr.expr)
                    if val.v is not None:
                        seen.add(self.ops.normalize_for_comparison(val.v))
                print("[DEBUG] Distinct values for COUNT(DISTINCT): ", seen)
                return Natural(len(seen))
            else:
                # COUNT(expr) - count non-NULL values
                count = 0
                for row in table.rows:
                    row_eta = eta.merge(Eta(row, table.cols))
                    val = self.run_expr(db, row_eta, agg_expr.expr)
                    if val.v is not None:
                        count += 1
                return Natural(count)

        elif isinstance(agg_expr, Sum):
            total = None
            use_decimal = False
            for row in table.rows:
                row_eta = eta.merge(Eta(row, table.cols))
                val = self.run_expr(db, row_eta, agg_expr.expr)
                if val.v is not None:
                    if total is None:
                        total = val.v
                        use_decimal = val.use_decimal
                    else:
                        total += val.v
            if total is None:
                return Nullv(None)
            return BValue(total, use_decimal)

        elif isinstance(agg_expr, Avg):
            total = None
            count = 0
            for row in table.rows:
                row_eta = eta.merge(Eta(row, table.cols))
                val = self.run_expr(db, row_eta, agg_expr.expr)
                if val is not None and val.v is not None:
                    if total is None:
                        total = val.v
                    else:
                        total += val.v
                    count += 1
            if count == 0:
                return Nullv(None)
            # Engine decides the AVG result type (e.g. T-SQL truncates integer AVG)
            return self.ops.avg_value(total, count, agg_expr.expr)

        elif isinstance(agg_expr, Max):
            max_val = None
            max_bval = None
            for row in table.rows:
                row_eta = eta.merge(Eta(row, table.cols))
                val = self.run_expr(db, row_eta, agg_expr.expr)
                if val.v is not None:
                    if max_val is None or val.v > max_val:
                        max_val = val.v
                        max_bval = val
            if max_val is None:
                return Nullv(None)
            return max_bval

        elif isinstance(agg_expr, Min):
            min_val = None
            min_bval = None
            for row in table.rows:
                row_eta = eta.merge(Eta(row, table.cols))
                val = self.run_expr(db, row_eta, agg_expr.expr)
                if val.v is not None:
                    if min_val is None or val.v < min_val:
                        min_val = val.v
                        min_bval = val
            if min_val is None:
                return Nullv(None)
            return min_bval

        else:
            raise Exception(f"Unknown aggregate: {agg_expr}")

    def eval_expr_with_aggregates(self, db, agg_expr, table: Table, eta: Eta):
        """Evaluate an expression that may contain aggregates, using eta for non-aggregates."""
        if isinstance(agg_expr, (Count, Sum, Avg, Max, Min)):
            return self.eval_aggregate(db, agg_expr, table, eta)
        elif isinstance(agg_expr, BValue):
            return agg_expr
        elif isinstance(agg_expr, NName):
            # Non-aggregate column reference - use the eta environment
            return eta.get(agg_expr.name)
        elif isinstance(agg_expr, Ascr):
            ep = self.eval_expr_with_aggregates(db, agg_expr.e, table, eta)
            return self.ops.cast(ep, agg_expr.t)
        elif isinstance(agg_expr, Op):
            #print("[DEBUG] Evaluating Op with aggregates: ", agg_expr, " in eta: ", eta)
            v1 = self.eval_expr_with_aggregates(db, agg_expr.e1, table, eta)
            v2 = self.eval_expr_with_aggregates(db, agg_expr.e2, table, eta)
            return self.ops.apply(agg_expr.op, v1, v2)
        elif isinstance(agg_expr, BNeg):
            bp = self.eval_expr_with_aggregates(db, agg_expr.b, table, eta)
            match bp.erase():
                case 1:
                    return Natural(0)
                case 0:
                    return Natural(1)
                case None:
                    return Nullv(None)
                case _:
                    return Boolean(not bp.erase())
        elif isinstance(agg_expr, And):
            v1 = self.eval_expr_with_aggregates(db, agg_expr.l, table, eta)
            v2 = self.eval_expr_with_aggregates(db, agg_expr.r, table, eta)
            if (v1.erase() == 0):
                return v1
            elif (v1.erase() == False):
                return v1
            elif(v1.v is None and v2.v != False):
                return v1
            return v2
        elif isinstance(agg_expr, Or):
            v1 = self.eval_expr_with_aggregates(db, agg_expr.l, table, eta)
            v2 = self.eval_expr_with_aggregates(db, agg_expr.r, table, eta)
            if (v1.erase() == 1):
                return v1
            elif (v1.erase() == True):
                return v1
            elif(v1.v is None and v2.v != True):
                return v1
            return v2
        else:
            # For other expressions, use the eta environment
            return self.run_expr(db, eta, agg_expr)

    def run_expr_having(self, db, row, attrnames, e: Expression, beta):
        """Evaluate expression in HAVING context where aggregates reference computed columns from GROUP BY."""
        #print("Evaluating HAVING expression:", e)
        #print("Current row:", row)
        #print("Current attrnames:", attrnames)
        #print("Current beta:", beta)
        # Find matching aggregate in beta and use that column value instead
        if isinstance(e, (Count, Sum, Avg, Max, Min)):
            # Try to find a matching aggregate in beta
            for i, alias in enumerate(beta.aliases):
                if self.aggregates_match(e, alias.e):
                    # Found matching aggregate - use the column value
                    return row[i]
            # No match found - this shouldn't happen if typechecker is correct
            raise Exception(f"Aggregate {e} in HAVING not found in SELECT")
        elif isinstance(e, BValue):
            return e
        elif isinstance(e, NName):
            return row[self.find_column_index(e.name, attrnames)]
        elif isinstance(e, BNeg):
            bp = self.run_expr_having(db, row, attrnames, e.b, beta)
            match bp.erase():
                case 1:
                    return Natural(0)
                case 0:
                    return Natural(1)
                case None:
                    return Nullv(None)
                case _:
                    return Boolean(not bp.erase())
        elif isinstance(e, Ascr):
            ep = self.run_expr_having(db, row, attrnames, e.e, beta)
            return self.ops.cast(ep, e.t)
        elif isinstance(e, Op):
            v1 = self.run_expr_having(db, row, attrnames, e.e1, beta)
            v2 = self.run_expr_having(db, row, attrnames, e.e2, beta)
            return self.ops.apply(e.op, v1, v2)
        elif isinstance(e, And):
            v1 = self.run_expr_having(db, row, attrnames, e.l, beta)
            v2 = self.run_expr_having(db, row, attrnames, e.r, beta)
            if (v1.erase() == 0):
                return v1
            elif (v1.erase() == False):
                return v1
            elif(v1.v is None and v2.v != False):
                return v1
            return v2
        elif isinstance(e, Or):
            v1 = self.run_expr_having(db, row, attrnames, e.l, beta)
            v2 = self.run_expr_having(db, row, attrnames, e.r, beta)
            if (v1.erase() == 1):
                return v1
            elif (v1.erase() == True):
                return v1
            elif(v1.v is None and v2.v != True):
                return v1
            return v2
        else:
            # For other expressions, use normal evaluation
            eta = Eta(row, attrnames)
            return self.run_expr(db, eta, e)

    def aggregates_match(self, e1, e2):
        """Check if two expressions are the same aggregate function."""
        if type(e1) != type(e2):
            return False
        if isinstance(e1, Count):
            if e1.expr is None and e2.expr is None:
                return True  # Both are COUNT(*)
            if e1.expr is not None and e2.expr is not None:
                return str(e1.expr) == str(e2.expr)  # Compare by string representation
            return False
        elif isinstance(e1, (Sum, Avg, Max, Min)):
            return str(e1.expr) == str(e2.expr)
        return False

    def changeb(self, v):
        if hasattr(self.ops, "truth_value"):
            return self.ops.truth_value(v)
        if v.erase() == 0:
            return False
        elif v.erase() == 1:
            return True
        elif v.erase() is None:
            return False
        else:
            return v.erase()

    def _logical_truth(self, v):
        if v.erase() is None:
            return None
        return bool(self.changeb(v))

    def run_query(self, db: Database, eta: Eta, q: Query) -> Table:
        #print("matching", q.__repr__())
        match q:
            case Rel():
                return db[q.tablename]
            case Eps():
                # DISTINCT: Execute subquery and remove duplicate rows
                subtable = self.run_query(db, eta, q.query)
                
                # Remove duplicates using dict to preserve order
                seen_dict = {}
                for row in subtable.rows:
                    # Convert row to comparable key
                    key = tuple(self.ops.normalize_for_comparison(bv.erase()) for bv in row)
                    if key not in seen_dict:
                        seen_dict[key] = row
                
                unique_rows = list(seen_dict.values())
                return Table(subtable.cols, unique_rows)
            case Proj():
                table = self.run_query(db, eta, q.query)
                es = q.beta.expressions()
                
                # Check if any expressions contain aggregates
                has_agg = any(self.has_aggregates(e) for e in es)
                
                if has_agg and not isinstance(q.query, GroupBy):
                    # Check if this is a HAVING case (Sel wrapping GroupBy)
                    is_having = isinstance(q.query, Sel) and isinstance(q.query.query, GroupBy)
                    
                    if is_having:
                        # HAVING case: Sel wraps GroupBy, and we have aggregates in projection
                        # The GroupBy has already been executed, table contains grouped results
                        # Just apply the projection
                        rowsvalue = list(map(lambda row: list(map(lambda e: self.run_expr(db, eta.merge(Eta(row, table.cols)), e), es)),
                                             table.rows))
                        names = q.beta.names()
                        return Table(names, rowsvalue)
                    else:
                        # Implicit aggregation: treat entire table as one group
                        # This handles cases like SELECT COUNT(*) FROM TA without GROUP BY
                        # or SELECT SUM(x) FROM TA WHERE condition
                        
                        # Use first row as representative (doesn't matter for pure aggregates)
                        # For empty tables, use None as group_row - aggregates will still work correctly
                        group_row = table.rows[0] if len(table.rows) > 0 else None
                        group_eta = eta if group_row is None else eta.merge(Eta(group_row, table.cols))
                        result_row = [self.eval_expr_with_aggregates(db, e, table, group_eta) for e in es]
                        return Table(q.beta.names(), [result_row])
                
                else:
                    # Normal projection without aggregates
                    # if isinstance(q.query, Sel) and q.query.isnull_not_null and self.ops.check_optimization():
                    #     es = q.beta.expressions()
                    #     def safe_eval(e, row):
                    #         try:
                    #             return self.run_expr(db, row, table.cols, e)
                    #         except:
                    #             return Nullv(None)
                    #
                    #     rowsvalue = list(map(
                    #         lambda row: list(map(lambda e: safe_eval(e, row), es)), table.rows))
                    #     return Table(q.beta.names(), rowsvalue)
                    
                    def eval_row(row): 
                        #print("[DEBUG] the merge of ", eta, row, table.cols, eta.merge(Eta(row, table.cols)))
                        return list(map(lambda e: self.run_expr(db, eta.merge(Eta(row, table.cols)), e), es))
                    rowsvalue = list(map(eval_row,
                                         table.rows))
                    names = q.beta.names()
                    return Table(names, rowsvalue)
            case Sel():
                # print(f"case Sel: {q}")
                q.isnull_not_null = q.cond.isnull_not_null

                # deal with null:
                condp = q.cond
                if condp.isnull:
                    condp = Nullv(None)

                ###################

                # Optimization: fuse filter into cross product to avoid materializing
                # the full cartesian product (e.g., 2000x2000 = 4M rows)
                if isinstance(q.query, Setop) and q.query.op == "X":
                    l = self.run_query(db, eta, q.query.l)
                    r = self.run_query(db, eta, q.query.r)
                    cols = l.cols + r.cols
                    filtered_rows = []
                    for li in l.rows:
                        for rj in r.rows:
                            combined = li + rj
                            row_eta = eta.merge(Eta(combined, cols))
                            expr_result = self.run_expr(db, row_eta, condp)
                            if self.changeb(expr_result):
                                filtered_rows.append(combined)
                    return Table(cols, filtered_rows)

                # Note: HAVING clauses are now handled inside GroupBy case
                # This Sel case only handles WHERE clauses

                table = self.run_query(db, eta, q.query)

                # Normal WHERE clause
                columns = table.cols

                def row_satisfies_condition(row):
                    row_eta = eta.merge(Eta(row, table.cols))
                    expr_result = self.run_expr(db, row_eta, condp)
                    boolean_result = self.changeb(expr_result)
                    return boolean_result

                filtered_rows = []
                for row in table.rows:
                    if row_satisfies_condition(row):
                        filtered_rows.append(row)

                tempt = Table(columns, filtered_rows)
                return tempt
            
            case GroupBy():
                # Execute the underlying query to get all rows
                # print("[DEBUG] Executing GROUP BY: ", q)
                # print("[DEBUG] Executing GROUP BY subquery: ", q.query)
                table = self.run_query(db, eta, q.query)
                
                # Group rows by grouping expressions
                groups = {}  # Dictionary: group_key -> list of rows
                print("[DEBUG] eta before grouping: ", eta)
                for row in table.rows:
                    # Evaluate grouping expressions for this row to get the group key
                    if len(q.grouping_exprs) == 0:
                        # No grouping expressions = single group
                        group_key = ()
                    else:
                        row_eta = eta.merge(Eta(row, table.cols))
                        group_key = tuple(
                            self.ops.normalize_for_comparison(self.run_expr(db, row_eta, expr).v)
                            for expr in q.grouping_exprs
                        )

                    # Add row to the appropriate group
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(row)

                # Implicit GROUP BY (no grouping expressions) must always produce one group,
                # even with no input rows (e.g., COUNT returns 0, SUM/AVG/MAX/MIN return NULL)
                if len(q.grouping_exprs) == 0 and len(groups) == 0:
                    groups[()] = []
                
                #Sort groups by their keys for deterministic ordering (DESC for PostgreSQL compatibility)
                # This makes GROUP BY results consistent and more likely to match PostgreSQL
                # Use a sort key that handles None values (NULLs last)
                def _group_sort_key(key):
                    return tuple((1, '') if v is None else (0, v) for v in key)
                sorted_group_keys = sorted(groups.keys(), key=_group_sort_key, reverse=True)
                
                # For each group, compute aggregate values and create result row
                result_rows = []
                es = q.beta.expressions()
                
                for group_key in sorted_group_keys:
                    group_rows = groups[group_key]
                    # Use first row of group as representative for non-aggregate columns
                    # For empty groups (implicit GROUP BY with no input rows), use a row of NULLs
                    if len(group_rows) > 0:
                        representative_row = group_rows[0]
                    else:
                        representative_row = [Nullv(None)] * len(table.cols)
                    
                    # Evaluate HAVING condition if present
                    if q.having_cond is not None:
                        having_eta = eta.merge(Eta(representative_row, table.cols))
                        having_result = self.eval_expr_with_aggregates(db, q.having_cond, Table(table.cols, group_rows), having_eta)
                        if not self.changeb(having_result):
                            continue  # Skip this group
                    
                    # Evaluate each expression in beta
                    result_row = []
                    for e in es:
                        group_eta = eta.merge(Eta(representative_row, table.cols))
                        value = self.eval_expr_with_aggregates(db, e, Table(table.cols, group_rows), group_eta)
                        result_row.append(value)
                    
                    result_rows.append(result_row)
                
                # Return table with result
                return Table(q.beta.names(), result_rows)
            
            case OrderBy():
                # ORDER BY: Sort result rows by specified expressions
                # Special handling for GROUP BY with aggregates in ORDER BY
                
                if isinstance(q.query, GroupBy) and any(self.has_aggregates(expr) for expr, _ in q.order_specs):
                    # GROUP BY with aggregates in ORDER BY: use hidden columns approach
                    groupby_query = q.query
                    
                    # Identify which ORDER BY expressions contain aggregates
                    hidden_order_indices = []
                    for i, (expr, direction) in enumerate(q.order_specs):
                        from interpreter.syntax.Syntax import Alias
                        actual_expr = expr.e if isinstance(expr, Alias) else expr
                        if self.has_aggregates(actual_expr):
                            hidden_order_indices.append(i)
                    
                    # Create extended beta with hidden ORDER BY aggregates
                    original_aliases = groupby_query.beta.aliases
                    extended_aliases = list(original_aliases)
                    
                    # Map order index to hidden column name
                    hidden_col_mapping = {}
                    for i in hidden_order_indices:
                        expr, direction = q.order_specs[i]
                        hidden_name = f"__order_{i}__"
                        hidden_col_mapping[i] = hidden_name
                        
                        from interpreter.syntax.Syntax import Alias
                        actual_expr = expr.e if isinstance(expr, Alias) else expr
                        extended_aliases.append(Alias(actual_expr, hidden_name))
                    
                    # Execute modified GROUP BY with extended beta
                    extended_beta = Beta(extended_aliases)
                    extended_groupby = GroupBy(extended_beta, groupby_query.grouping_exprs, groupby_query.query)
                    extended_table = self.run_query(db, eta, extended_groupby)
                    
                    # Sort using hidden columns
                    rows_with_keys = []
                    for row in extended_table.rows:
                        sort_keys = []
                        for i, (expr, direction) in enumerate(q.order_specs):
                            if i in hidden_col_mapping:
                                # Use hidden column value
                                hidden_name = hidden_col_mapping[i]
                                col_idx = extended_table.cols.index(hidden_name)
                                sort_value = row[col_idx]
                                comp_value = sort_value.erase() if hasattr(sort_value, 'erase') else sort_value
                            else:
                                # Evaluate simple expression
                                from interpreter.syntax.Syntax import Alias
                                actual_expr = expr.e if isinstance(expr, Alias) else expr
                                row_eta = eta.merge(Eta(row, extended_table.cols))
                                sort_value = self.run_expr(db, row_eta, actual_expr)
                                comp_value = sort_value.erase() if hasattr(sort_value, 'erase') else sort_value
                            
                            # Create sort key
                            # NULL: (0,) for DESC (NULLs first), (1,) for ASC (NULLs last)
                            # Non-NULL: (1, ...) for DESC, (0, value) for ASC
                            # This ensures NULL and non-NULL never share the same first element,
                            # avoiding TypeError when Python compares None with a value.
                            if comp_value is None:
                                sort_key = (0,) if direction == 'DESC' else (1,)
                            else:
                                if direction == 'ASC':
                                    sort_key = (0, comp_value)
                                else:
                                    from decimal import Decimal
                                    if isinstance(comp_value, (int, float, Decimal)):
                                        sort_key = (1, -comp_value)
                                    else:
                                        sort_key = (1, _ReverseKey(comp_value))

                            sort_keys.append(sort_key)

                        rows_with_keys.append((tuple(sort_keys), row))

                    # Sort rows
                    sorted_rows = sorted(rows_with_keys, key=lambda x: x[0])
                    
                    # Remove hidden columns and return original columns only
                    original_col_count = len(original_aliases)
                    final_rows = [row[:original_col_count] for _, row in sorted_rows]
                    original_col_names = [alias.name for alias in original_aliases]
                    
                    return Table(original_col_names, final_rows)
                
                else:
                    # Normal ORDER BY without GROUP BY aggregates
                    subtable = self.run_query(db, eta, q.query)
                    
                    if not subtable.rows:
                        return subtable

                    aggregate_sort_cache = {}
                    
                    # Compute sort keys for each row
                    rows_with_keys = []
                    for row in subtable.rows:
                        sort_keys = []
                        for expr, direction in q.order_specs:
                            from interpreter.syntax.Syntax import Alias
                            actual_expr = expr.e if isinstance(expr, Alias) else expr

                            if self.has_aggregates(actual_expr):
                                cache_key = repr(actual_expr)
                                if cache_key not in aggregate_sort_cache:
                                    aggregate_sort_cache[cache_key] = self.eval_expr_with_aggregates(
                                        db, actual_expr, subtable, Eta([], [])
                                    )
                                sort_value = aggregate_sort_cache[cache_key]
                            else:
                                row_eta = eta.merge(Eta(row, subtable.cols))
                                sort_value = self.run_expr(db, row_eta, actual_expr)
                            comp_value = sort_value.erase() if hasattr(sort_value, 'erase') else sort_value
                            
                            # NULL: (0,) for DESC (NULLs first), (1,) for ASC (NULLs last)
                            # Non-NULL: (1, ...) for DESC, (0, value) for ASC
                            # This ensures NULL and non-NULL never share the same first element,
                            # avoiding TypeError when Python compares None with a value.
                            if comp_value is None:
                                sort_key = (0,) if direction == 'DESC' else (1,)
                            else:
                                if direction == 'ASC':
                                    sort_key = (0, comp_value)
                                else:
                                    from decimal import Decimal
                                    if isinstance(comp_value, (int, float, Decimal)):
                                        sort_key = (1, -comp_value)
                                    else:
                                        sort_key = (1, _ReverseKey(comp_value))

                            sort_keys.append(sort_key)

                        rows_with_keys.append((tuple(sort_keys), row))

                    sorted_rows = sorted(rows_with_keys, key=lambda x: x[0])
                    final_rows = [row for _, row in sorted_rows]
                    
                    return Table(subtable.cols, final_rows)
            
            case Limit():
                # LIMIT: Execute subquery and limit the number of rows
                subtable = self.run_query(db, eta, q.query)
                
                # Apply offset and limit to rows
                start = q.offset
                end = q.offset + q.limit_count
                limited_rows = subtable.rows[start:end]
                
                return Table(subtable.cols, limited_rows)
            
            case Setop():
                l = None
                r = None
                l_error = None
                r_error = None

                try:
                    l = self.run_query(db, eta, q.l)
                except Exception as e:
                    l_error = e

                try:
                    r = self.run_query(db, eta, q.r)
                except Exception as e:
                    r_error = e

                if l is not None and l.rows == [] and self.ops.check_optimization() and (q.op in ("∩", "-")):
                    return l
                # elif r is not None and r.rows == [] and self.ops.check_optimization() and (q.op in ("∩", "-")):
                #     return r
                elif l_error is not None:
                    raise Exception(l_error)
                elif r_error is not None:
                    raise Exception(r_error)
                match q.op:
                    case "X":
                        result = []
                        for i in l.rows:
                            for j in r.rows:
                                result.append(i + j)
                        return Table(l.cols + r.cols, result)
                    case "∪":
                        def eraseRow(r):
                            res = []
                            for vc in r:
                                res.append(vc.v)
                            return res

                        def eraseRows(rs):
                            res = []
                            for r in rs:
                                res.append(eraseRow(r))
                            return res

                        rows = l.rows + (list(filter(lambda x: not (eraseRow(x) in eraseRows(l.rows)), r.rows)))
                        res = [lst for i, lst in enumerate(rows) if eraseRow(lst) not in eraseRows(rows[:i])]
                        return Table(l.cols, res)
                    case "∩":
                        def eraseRow(r):
                            res = []
                            for vc in r:
                                res.append(vc.v)
                            return res

                        def eraseRows(rs):
                            res = []
                            for r in rs:
                                res.append(eraseRow(r))
                            return res

                        rows = (list(filter(lambda x: eraseRow(x) in eraseRows(r.rows), l.rows)))
                        res = [lst for i, lst in enumerate(rows) if eraseRow(lst) not in eraseRows(rows[:i])]
                        return Table(l.cols, res)
                    case "-":
                        def eraseRow(r):
                            res = []
                            for vc in r:
                                res.append(vc.v)
                            return res

                        def eraseRows(rs):
                            res = []
                            for r in rs:
                                res.append(eraseRow(r))
                            return res

                        rows = (list(filter(lambda x: not (eraseRow(x) in eraseRows(r.rows)), l.rows)))
                        res = [lst for i, lst in enumerate(rows) if eraseRow(lst) not in eraseRows(rows[:i])]
                        return Table(l.cols, res)
            case _:
                raise Exception(f"Running Query Error: {q}")

    def run_expr(self, db, eta: Eta, e: Expression) -> BValue:
        match e:
            case BValue():  # (Tv)
                return BValue(e.v, e.use_decimal)
            case NName():  # (TN)
                return eta.get(e.name)
            case BNeg():
                bp = self.run_expr(db, eta, e.b)
                if getattr(self.ops, "use_truth_value_for_logical_ops", False):
                    truth = self._logical_truth(bp)
                    if truth is None:
                        return Nullv(None)
                    return self.ops.boolean_value(not truth)
                match bp.erase():
                    case 1:
                        return Natural(0)
                    case 0:
                        return Natural(1)
                    case None:
                        return Nullv(None)
                    case _:
                        return Boolean(not bp.erase())
            case Ascr():
                ep = self.run_expr(db, eta, e.e)
                return self.ops.cast(ep, e.t)
            case Op():
                v1 = self.run_expr(db, eta, e.e1)
                v2 = self.run_expr(db, eta, e.e2)
                v = self.ops.apply(e.op, v1, v2)
                return v
            case And():
                v1 = self.run_expr(db, eta, e.l)
                if (
                    getattr(self.ops, "use_truth_value_for_logical_ops", False)
                    and getattr(self.ops, "short_circuit_logical_ops", False)
                ):
                    t1 = self._logical_truth(v1)
                    if t1 is False:
                        return self.ops.boolean_value(False)
                    v2 = self.run_expr(db, eta, e.r)
                    t2 = self._logical_truth(v2)
                    if t2 is False:
                        return self.ops.boolean_value(False)
                    if t1 is None or t2 is None:
                        return Nullv(None)
                    return self.ops.boolean_value(True)
                v2 = self.run_expr(db, eta, e.r)
                if not getattr(self.ops, "use_truth_value_for_logical_ops", False):
                    if (v1.erase() == 0):
                        return v1
                    elif (v1.erase() == False):
                        return v1
                    elif(v1.v is None and v2.v != False):
                        # vv = self.ops.boolean_value(False) here i change for null
                        return v1
                    # elif(v2.v is None):
                    #     return v2
                    return v2
                t1 = self._logical_truth(v1)
                t2 = self._logical_truth(v2)
                if t1 is False or t2 is False:
                    return self.ops.boolean_value(False)
                if t1 is None or t2 is None:
                    return Nullv(None)
                return self.ops.boolean_value(True)
            case Or():
                v1 = self.run_expr(db, eta, e.l)
                if (
                    getattr(self.ops, "use_truth_value_for_logical_ops", False)
                    and getattr(self.ops, "short_circuit_logical_ops", False)
                ):
                    t1 = self._logical_truth(v1)
                    if t1 is True:
                        return self.ops.boolean_value(True)
                    v2 = self.run_expr(db, eta, e.r)
                    t2 = self._logical_truth(v2)
                    if t2 is True:
                        return self.ops.boolean_value(True)
                    if t1 is None or t2 is None:
                        return Nullv(None)
                    return self.ops.boolean_value(False)
                v2 = self.run_expr(db, eta, e.r)
                if not getattr(self.ops, "use_truth_value_for_logical_ops", False):
                    if (v1.erase() == 1):
                        return v1
                    elif (v1.erase() == True):
                        return v1
                    elif(v1.v is None and v2.v != True):
                        return v1
                    return v2
                t1 = self._logical_truth(v1)
                t2 = self._logical_truth(v2)
                if t1 is True or t2 is True:
                    return self.ops.boolean_value(True)
                if t1 is None or t2 is None:
                    return Nullv(None)
                return self.ops.boolean_value(False)
            case Empty():
                ep = e.q
                ep.beta = Beta([Alias(Natural(1), '1')])
                t = self.run_query(db, eta, ep)
                b = self.ops.doEmpty(t)
                return b
            case Ins():
                r = []
                fresh_eta = Eta([], [])
                #table = self.run_query(db, fresh_eta, e.q)
                #print("[DEBUG] Running subquery for IN expression:", e.q)
                #print("[DEBUG] passing as eta the following:", eta)
                table = self.run_query(db, eta, e.q)
                #print("[DEBUG] Subquery result for IN expression:", table)
                #print("")
                if table.rows == []:
                    return BValue(False)
                else:
                    for i, expr in enumerate(e.es):
                        v = self.run_expr(db, eta, expr)
                        r.append(v)
                    b = self.ops.doIn(r, table.rows)
                    return b
            case ScalarSubquery():
                # Execute the subquery and ensure it returns exactly one row
                table = self.run_query(db, eta, e.query)
                if len(table.rows) == 0:
                    # Empty result - return NULL
                    return Nullv(None)
                elif len(table.rows) > 1:
                    if self.ops.__class__.__name__ == "SqliteOps":
                        return table.rows[0][0]
                    # More than one row - this is an error
                    raise Exception(f"Scalar subquery returned {len(table.rows)} rows, expected exactly 1")
                # Return the single value from the first (and only) row
                return table.rows[0][0]
            case IsNull():
                v = self.run_expr(db, eta, e.e)
                return self.ops.isnull_res(v)


        raise Exception(f"Not implemented Expression Error: {e}")

    # def apply(self, op, v1: BValue, v2: BValue) -> BValue:
    #     """
    #     This function corresponds to the apply
    #     """
    #     raise Exception(f"'Apply' function not implemented")

    # def doEmpty(self, t):
    #     return BValue(True if t.rows != [] else False)
    #
    # def doIn(self, es, rs, db, row, attrnames, sql):
    #     for r in rs:
    #         eq = True
    #         for i, e in enumerate(es):
    #             rr = r[i]
    #             bb = self.apply("=", e, rr)
    #             if not (bb.erase()):
    #                 eq = False
    #                 break
    #         if eq:
    #             return BValue(eq)
    #     return BValue(False)

#
# 1. without any simplification
# 2. with all simplification
