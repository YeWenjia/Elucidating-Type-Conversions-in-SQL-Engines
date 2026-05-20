from typing import Tuple

from interpreter import AbstractOps
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression import Expression
from interpreter.syntax.expression.NName import NName
from interpreter.syntax.expression.Op import *
from interpreter.syntax.expression.BNeg import BNeg
from interpreter.syntax.type.RelationType import *
from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.And import And
from interpreter.syntax.expression.Or import Or
from interpreter.syntax.expression.Empty import Empty
from interpreter.syntax.expression.Ins import Ins
from interpreter.syntax.expression.ScalarSubquery import ScalarSubquery
from interpreter.syntax.type.ValueType import *
from interpreter.syntax.expression.IsNull import IsNull
from interpreter.syntax.expression.aggregation import Count, Sum, Avg, Max, Min



class DuplicateNameError(Exception):
    pass


class TypeError(Exception):
    pass


TypeResultQuery = Tuple[RelationType, Query]
TypeResultBeta = Tuple[RelationType, Beta]
TypeResultExpr = Tuple[ValueType, Expression]


class Typechecker:
    # ops: AbstractOps

    def __init__(self, ops: AbstractOps):
        self.ops = ops
        self.freshindex = 0

    def typecheck_query(self, schema, T: RelationType, q: Query) -> TypeResultQuery:
        # print(q)
        match q:
            case Rel():
                return schema[q.tablename], q
            case Eps():
                # DISTINCT: Type is same as subquery, just remove duplicates
                T, Q = self.typecheck_query(schema, T, q.query)
                return T, Eps(Q)
            case Proj():
                Tpp, Q = self.typecheck_query(schema, T, q.query)
                Tp, beta = self.typecheck_aexpr(schema, T.concat(self.ops.clean(Tpp)), q.beta)
                return Tp, Proj(beta, Q)
            case Sel():
                # print(f"case Sel: {q}")
                Tp, Q = self.typecheck_query(schema, T, q.query)
                
                # Special handling for HAVING (Sel wrapping GroupBy)
                if isinstance(Q, GroupBy):
                    # This is a HAVING clause - aggregates in condition should be typechecked
                    # against the underlying query's schema, not the GroupBy output schema
                    #T_underlying, Q_underlying = self.typecheck_query(schema, Tp, Q.query)
                    t, theta = self.typecheck_expr_having(schema, Tp, T.concat(Tp), q.cond)
                    self.ops.check_boolean(t, theta)
                    return Tp, Sel(theta, Q)
                else:
                    # Normal WHERE clause
                    t, theta = self.typecheck_expr(schema, T.concat(Tp), q.cond)
                    self.ops.check_boolean(t, theta)
                    return Tp, Sel(theta, Q)
            case Setop() if q.op in ["∪", "∩", "-"]:
                match (q.l, q.r):
                    case (Proj(), Proj()):
                        T1, Q1 = self.typecheck_query(schema, T, q.l)
                        T2, Q2 = self.typecheck_query(schema, T, q.r)
                        beta1 = q.l.beta
                        beta2 = q.r.beta
                        T = self.biconvs(beta1, T1, beta2, T2)
                        match (Q1, Q2):
                            case (Proj(), Proj()):
                                return T, Setop(q.op,
                                                Proj(self.inserts(Q1.beta, T, q.op), Q1.query),
                                                Proj(self.inserts(Q2.beta, T, q.op), Q2.query))
                            case _:
                                raise Exception(f"Typecheck Setop Query Error: {q}")
                    case _:
                        raise Exception(f"Typecheck Setop Query Error between {q.l.__repr__()} and {q.r.__repr__()}")

            case Setop() if q.op == "X":
                left_cols = q.l.get_col_names()
                right_cols = q.r.get_col_names()
                com = list(set(left_cols).intersection(right_cols))
                if len(com) <= 0:
                    T1, Q1 = self.typecheck_query(schema, T, q.l)
                    T2, Q2 = self.typecheck_query(schema, T, q.r)
                    return RelationType(T1.nametypes + T2.nametypes), Setop("X", Q1, Q2)
                else:
                    raise Exception(f"Typecheck Product Query Error: {q}")
            
            case GroupBy():
                # Typecheck the underlying query first
                Tp, Q = self.typecheck_query(schema, T, q.query)
                
                # Typecheck grouping expressions
                grouping_exprs_checked = []
                for expr in q.grouping_exprs:
                    _, expr_checked = self.typecheck_expr(schema, Tp, expr)
                    grouping_exprs_checked.append(expr_checked)
                
                # Typecheck the beta (projection with aggregates)
                # The beta should only reference:
                # 1. Grouping columns (from grouping_exprs)
                # 2. Aggregate functions
                Tpp, beta_checked = self.typecheck_aexpr(schema, self.ops.clean(T.concat(Tp)), q.beta)
                
                # Typecheck HAVING condition if present
                having_cond_checked = None
                if q.having_cond is not None:
                    Tcond, having_cond_checked = self.typecheck_expr(schema, T.concat(Tp), q.having_cond)
                    self.ops.check_boolean(Tcond, having_cond_checked)
                   
                
                return Tpp, GroupBy(beta_checked, grouping_exprs_checked, Q, having_cond_checked)
            
            case OrderBy():
                # ORDER BY: Type is same as subquery, just reorders rows
                T_underlying, Q = self.typecheck_query(schema, T, q.query)
                #print("[DEBUG] Typecheck OrderBy: underlying query type:", T_underlying)
                
                # Special handling for GROUP BY with aggregates in ORDER BY
                if isinstance(Q, GroupBy):
                    # When subquery is GroupBy, ORDER BY can contain aggregates
                    # These aggregates should be typechecked against the underlying query schema
                    #, _ = self.typecheck_query(schema, T, Q.query)
                    
                    typed_specs = []
                    for expr, direction in q.order_specs:
                        from interpreter.syntax.Syntax import Alias
                        from interpreter.syntax.expression.aggregation import Count, Sum, Avg, Max, Min
                        
                        # Check if expression contains aggregates
                        actual_expr = expr.e if isinstance(expr, Alias) else expr
                        is_aggregate = isinstance(actual_expr, (Count, Sum, Avg, Max, Min))
                        
                        if is_aggregate:
                            # Typecheck aggregate against underlying schema (before grouping)
                            #print("[DEBUG] Typecheck OrderBy: non-aggregate expression in ORDER BY, typechecking against grouped schema", T, T_underlying, actual_expr)
                            _, expr_checked = self.typecheck_expr(schema, T_underlying, actual_expr)
                        else:
                            # Typecheck against grouped result schema
                            _, expr_checked = self.typecheck_expr(schema, T_underlying, actual_expr)
                        
                        if isinstance(expr, Alias):
                            typed_expr = Alias(expr_checked, expr.name)
                        else:
                            typed_expr = expr_checked
                        
                        typed_specs.append((typed_expr, direction))
                else:
                    # Normal ORDER BY without GROUP BY
                    typed_specs = []
                    for expr, direction in q.order_specs:
                        from interpreter.syntax.Syntax import Alias
                        actual_expr = expr.e if isinstance(expr, Alias) else expr
                        
                        _, expr_checked = self.typecheck_expr(schema, T_underlying, actual_expr)
                        
                        if isinstance(expr, Alias):
                            typed_expr = Alias(expr_checked, expr.name)
                        else:
                            typed_expr = expr_checked
                        
                        typed_specs.append((typed_expr, direction))
                
                return T_underlying, OrderBy(Q, typed_specs)
            
            case Limit():
                # LIMIT: Type is same as subquery, just limits rows
                T, Q = self.typecheck_query(schema, T, q.query)
                
                # Validate limit and offset are non-negative
                if q.limit_count < 0:
                    raise TypeError(f"LIMIT must be non-negative, got {q.limit_count}")
                if q.offset < 0:
                    raise TypeError(f"OFFSET must be non-negative, got {q.offset}")
                
                return T, Limit(Q, q.limit_count, q.offset)
        raise Exception(f"Typecheck Query Error: {q}")

    def typecheck_aexpr(self, schema, T: RelationType, beta: Beta) -> TypeResultBeta:
        # NOTE: We used to check for uniqueness of display names here, but now Beta constructor
        # automatically makes internal names unique by adding #N suffixes to duplicates.
        # Display names can be duplicates (like PostgreSQL allows), but internal names are unique.
        return RelationType([NameType(alias.internal_name, self.typecheck_expr(schema, T, alias.e)[0]) for alias in beta.aliases]), \
            Beta([Alias(self.typecheck_expr(schema, T, alias.e)[1], alias.name, alias.internal_name) for alias in beta.aliases])

    def typecheck_expr(self, schema, T: RelationType, e: Expression) -> TypeResultExpr:
        match e:
            case BValue():  # (Tv)
                return self.ops.ty(e), Ascr(e, self.ops.ty(e))
            case NName():  # (TN)
                #print("looking for column:", e.name, " in ", T)
                return T.getTypeByName(e.name), e
            case BNeg():
                t, bp = self.typecheck_expr(schema, T, e.b)
                return self.ops.check_boolean(t, bp), BNeg(bp)
            case Ascr():
                tp, ep = self.typecheck_expr(schema, T, e.e)
                if self.ops.explicit_cast_feasibility(e.e, tp, e.t):
                    return e.t, Ascr(ep, e.t)
                else:
                    raise Exception(f"Typecheck Ascription Error: {e}")
            case Op():
                t1, e1p = self.typecheck_expr(schema, T, e.e1)
                t2, e2p = self.typecheck_expr(schema, T, e.e2)
                t: FuncType = self.ops.resolve(e.e1, t1, e.e2, t2, e.op)
                return t.cod, self.ops.insert(Op(e.op,
                                                 self.ops.insert(e1p, t.dom[0], e.op),
                                                 self.ops.insert(e2p, t.dom[1], e.op)),
                                              t.cod, e.op)
            case And():
                t1, bp1 = self.typecheck_expr(schema, T, e.l)
                t2, bp2 = self.typecheck_expr(schema, T, e.r)
                self.ops.check_boolean(t1, bp1)
                self.ops.check_boolean(t2, bp2)
                return self.ops.check_boolean(t1, bp1), And(bp1, bp2)
            case Or():
                t1, bp1 = self.typecheck_expr(schema, T, e.l)
                t2, bp2 = self.typecheck_expr(schema, T, e.r)
                self.ops.check_boolean(t1, bp1)
                self.ops.check_boolean(t2, bp2)
                return self.ops.check_boolean(t1, bp1), Or(bp1, bp2)
            case Empty():
                t, qp = self.typecheck_query(schema, T, e.q)
                return self.ops.restype_E(), Empty(qp)
            case Ins():
                tt2, q = self.typecheck_query(schema, T, e.q)
                ex_tt = []
                self.freshindex += 1
                cols = []
                for i, tbt in enumerate(tt2.nametypes):
                    oldname = tbt.name
                    newname = f"{'N'}{self.freshindex}{'.'}{oldname}"
                    tbt.name = newname
                    ex_tt.append(tbt)
                    col = Alias(NName(oldname), newname)
                    cols.append(col)
                rt = self.ops.clean(RelationType(ex_tt))
                ex_tt = rt.nametypes
                r_eqs = []

                # Typecheck each side of the IN-equality with its own scope.
                # The outer expression must resolve against the unmodified outer
                # scope `T` — appending the renamed subquery columns would make
                # an unqualified name like `party_id` ambiguous and resolve to
                # the inner column's type rather than the outer's.
                for i, ep in enumerate(e.es):
                    t_left, ep_checked = self.typecheck_expr(schema, T, ep)
                    t_right = ex_tt[i].type
                    ft = self.ops.resolve(ep, t_left, NName(ex_tt[i].name), t_right, "=")
                    r_eqs.append(self.ops.insert(
                        Op("=",
                           self.ops.insert(ep_checked, ft.dom[0], "="),
                           self.ops.insert(NName(ex_tt[i].name), ft.dom[1], "=")),
                        ft.cod, "="))

                lft_exps = []
                rgt_exps = []
                for i, eq in enumerate(r_eqs):
                    if isinstance(eq, Op):
                        lft_exps.append(eq.e1)
                        rgt_exps.append(eq.e2)
                    else:
                        lft_exps.append(eq.e.e1)
                        rgt_exps.append(eq.e.e2)

                lft = lft_exps
                rgt1 = Proj(Beta(cols), q)
                rgt2 = []

                for i, c in enumerate(cols):
                    rgt2.append(Alias((rgt_exps[i]), c.name))

                rgt = Proj(Beta(rgt2), rgt1)
                return self.ops.restype_E(), Ins(lft, rgt)
            case IsNull():
                t, ep = self.typecheck_expr(schema, T, e.e)
                return self.ops.restype_E(), IsNull(ep)
            case ScalarSubquery():
                # Typecheck the subquery and ensure it returns exactly one column
                tt, qp = self.typecheck_query(schema, T, e.query)
                if len(tt.nametypes) != 1:
                    raise TypeError(f"Scalar subquery must return exactly one column, got {len(tt.nametypes)}")
                # Return the type of the single column and wrap the typechecked query
                col_type = tt.nametypes[0].type
                return col_type, ScalarSubquery(qp)
            case Count():
                # Count always returns ZType (integer)
                # Count can have expr=None for COUNT(*) or an expression for COUNT(col)
                if e.expr is not None:
                    t, ep = self.typecheck_expr(schema, T, e.expr)
                    return ZType(), Count(ep, distinct=e.distinct)
                else:
                    # COUNT(*)
                    return ZType(), Count(None, distinct=e.distinct)
            case Sum():
                # Sum returns the same type as the input expression
                t, ep = self.typecheck_expr(schema, T, e.expr)
                # call to insert to insert a cast given the operator
                t: FuncType = self.ops.resolve_agg_func(e.expr, t, "SUM")
                return t.cod, Sum(self.ops.insert(ep, t.dom, "SUM"))

            case Avg():
                # Avg always returns RType (real/decimal)
                t, ep = self.typecheck_expr(schema, T, e.expr)
                t: FuncType = self.ops.resolve_agg_func(e.expr, t, "AVG")
                return RType(), Avg(self.ops.insert(ep, t.dom, "AVG"))
                
            case Max():
                # Max returns the same type as the input expression
                t, ep = self.typecheck_expr(schema, T, e.expr)
                return t, Max(ep)
            case Min():
                # Min returns the same type as the input expression
                t, ep = self.typecheck_expr(schema, T, e.expr)
                return t, Min(ep)



        raise Exception(f"Not implemented Expression Error: {e}")

    def typecheck_expr_having(self, schema, T_grouped, T_underlying, e: Expression) -> TypeResultExpr:
        """
        Typecheck expression in HAVING context.
        T_grouped: schema from GroupBy output (has aggregated columns)
        T_underlying: schema from GroupBy input (has original table columns)
        """
        match e:
            case BValue():
                return self.ops.ty(e), Ascr(e, self.ops.ty(e))
            case NName():
                # Column references in HAVING can reference output columns
                return T_grouped.getTypeByName(e.name), e
            case BNeg():
                t, bp = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.b)
                return self.ops.check_boolean(t, bp), BNeg(bp)
            case Ascr():
                tp, ep = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.e)
                if self.ops.explicit_cast_feasibility(e.e, tp, e.t):
                    return e.t, Ascr(ep, e.t)
                else:
                    raise Exception(f"Typecheck Ascription Error: {e}")
            case Op():
                t1, e1p = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.e1)
                t2, e2p = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.e2)
                t: FuncType = self.ops.resolve(e.e1, t1, e.e2, t2, e.op)
                return t.cod, self.ops.insert(Op(e.op,
                                                 self.ops.insert(e1p, t.dom[0], e.op),
                                                 self.ops.insert(e2p, t.dom[1], e.op)),
                                              t.cod, e.op)
            case And():
                t1, bp1 = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.l)
                t2, bp2 = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.r)
                self.ops.check_boolean(t1, bp1)
                self.ops.check_boolean(t2, bp2)
                return self.ops.check_boolean(t1, bp1), And(bp1, bp2)
            case Or():
                t1, bp1 = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.l)
                t2, bp2 = self.typecheck_expr_having(schema, T_grouped, T_underlying, e.r)
                self.ops.check_boolean(t1, bp1)
                self.ops.check_boolean(t2, bp2)
                return self.ops.check_boolean(t1, bp1), Or(bp1, bp2)
            case Count():
                # aggregates in HAVING: typecheck against underlying schema
                if e.expr is not None:
                    t, ep = self.typecheck_expr(schema, T_underlying, e.expr)
                    return ZType(), Count(ep, distinct=e.distinct)
                else:
                    return ZType(), Count(None, distinct=e.distinct)
            case Sum():
                t, ep = self.typecheck_expr(schema, T_underlying, e.expr)
                if not isinstance(t, (ZType, RType)):
                    raise Exception(f"SUM requires numeric type, got {t}")
                return t, Sum(ep)
            case Avg():
                t, ep = self.typecheck_expr(schema, T_underlying, e.expr)
                if not isinstance(t, (ZType, RType)):
                    raise Exception(f"AVG requires numeric type, got {t}")
                return RType(), Avg(ep)
            case Max():
                t, ep = self.typecheck_expr(schema, T_underlying, e.expr)
                return t, Max(ep)
            case Min():
                t, ep = self.typecheck_expr(schema, T_underlying, e.expr)
                return t, Min(ep)
        
        raise Exception(f"Not implemented Expression in HAVING Error: {e}")

    def unique(self, names: list[str]):
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if names[i] == names[j]:
                    raise DuplicateNameError(f"Duplicate Alias Error: {names[i]}")


    def biconvs(self, beta1: Beta, T1: RelationType, beta2: Beta, T2: RelationType):
        """
        This function corresponds to biconv* of the paper, and it is used to compute the
        bidirectional conversion between two list of aliased expressions
        """
        tt1 = T1.nametypes
        tt2 = T2.nametypes

        def getSetOperator(ts):
            e1 = ts[0].e
            e2 = ts[1].e
            t1 = ts[2].type
            t2 = ts[3].type
            return (ts[2].name, self.ops.biconv(e1, t1, e2, t2))

        if len(beta1.aliases) == len(beta2.aliases):
            try:
                zipped = zip(beta1.aliases, beta2.aliases, tt1, tt2)
                return RelationType(
                    list(map(lambda y: NameType(y[0], y[1]), map(lambda x: getSetOperator(x), list(zipped)))))
            except ValueError:
                raise Exception('They do not have the same number of columns!')
        else:
            raise Exception('They do not have the same number of columns!')

    def inserts(self, beta: Beta, T: RelationType, op: str) -> Beta:
        """
        This function corresponds to insert* in the paper.
        It calls insert over all the expressions on beta
        """
        return Beta(
            [Alias(self.ops.insert(alias.e, T.nametypes[i].type, op), alias.name) for i, alias in
             enumerate(beta.aliases)])
