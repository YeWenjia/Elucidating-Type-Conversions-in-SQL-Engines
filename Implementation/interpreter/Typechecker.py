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
from interpreter.syntax.type.ValueType import *
from interpreter.syntax.expression.IsNull import IsNull



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

    def typecheck_query(self, schema, q: Query) -> TypeResultQuery:
        # print(q)
        match q:
            case Rel():
                return schema[q.tablename], q
            case Proj():
                # print(f"case Proj: {q}")
                T, Q = self.typecheck_query(schema, q.query)
                Tp, beta = self.typecheck_aexpr(schema, self.ops.clean(T), q.beta)
                return Tp, Proj(beta, Q)
            case Sel():
                # print(f"case Sel: {q}")
                T, Q = self.typecheck_query(schema, q.query)
                t, theta = self.typecheck_expr(schema, T, q.cond)
                self.ops.check_boolean(t)
                return T, Sel(theta, Q)
            case Setop() if q.op in ["∪", "∩", "-"]:
                match (q.l, q.r):
                    case (Proj(), Proj()):
                        T1, Q1 = self.typecheck_query(schema, q.l)
                        T2, Q2 = self.typecheck_query(schema, q.r)
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
                        raise Exception(f"Typecheck Setop Query Error: {q}")

            case Setop() if q.op == "X":
                left_cols = q.l.get_col_names()
                right_cols = q.r.get_col_names()
                com = list(set(left_cols).intersection(right_cols))
                if len(com) <= 0:
                    T1, Q1 = self.typecheck_query(schema, q.l)
                    T2, Q2 = self.typecheck_query(schema, q.r)
                    return RelationType(T1.nametypes + T2.nametypes), Setop("X", Q1, Q2)
                else:
                    raise Exception(f"Typecheck Product Query Error: {q}")
        raise Exception(f"Typecheck Query Error: {q}")

    def typecheck_aexpr(self, schema, T: RelationType, beta: Beta) -> TypeResultBeta:
        # check for uniqueness of names
        self.unique([alias.name for alias in beta.aliases])
        return RelationType([NameType(alias.name, self.typecheck_expr(schema, T, alias.e)[0]) for alias in beta.aliases]), \
            Beta([Alias(self.typecheck_expr(schema, T, alias.e)[1], alias.name) for alias in beta.aliases])

    def typecheck_expr(self, schema, T: RelationType, e: Expression) -> TypeResultExpr:
        match e:
            case BValue():  # (Tv)
                return self.ops.ty(e), Ascr(e, self.ops.ty(e))
            case NName():  # (TN)
                return T.getTypeByName(e.name), e
            case BNeg():
                t, bp = self.typecheck_expr(schema, T, e.b)
                return self.ops.check_boolean(t), BNeg(bp)
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
                self.ops.check_boolean(t1)
                self.ops.check_boolean(t2)
                return self.ops.check_boolean(t1), And(bp1, bp2)
            case Or():
                t1, bp1 = self.typecheck_expr(schema, T, e.l)
                t2, bp2 = self.typecheck_expr(schema, T, e.r)
                self.ops.check_boolean(t1)
                self.ops.check_boolean(t2)
                return self.ops.check_boolean(t1), Or(bp1, bp2)
            case Empty():
                t, qp = self.typecheck_query(schema, e.q)
                return self.ops.restype_E(), Empty(qp)
            case Ins():
                tt2, q = self.typecheck_query(schema, e.q)
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
                tempt_tablet = T
                tempt_tablet.nametypes += ex_tt
                r_eqs = []

                for i, ep in enumerate(e.es):
                    ee = Eq(ep, NName(ex_tt[i].name))
                    t, r_e = self.typecheck_expr(schema, tempt_tablet, ee)
                    r_eqs.append(r_e)

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



        raise Exception(f"Not implemented Expression Error: {e}")

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
