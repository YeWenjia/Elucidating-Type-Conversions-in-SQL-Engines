from interpreter.syntax.expression.BExpr import *
from interpreter.syntax.Syntax import *
from interpreter.syntax.expression.Op import *
from interpreter.syntax.expression.NName import *

freshindex = 0

class Ins(BExpr):
    def __init__(self, es, q):
        self.es = es
        self.q = q

    def __str__(self):
        return "(" + str(self.es) + " in " + str(self.q) + ")"

    def __eq__(self, other):
        return self.q == other.q and self.es == other.es

    def run(self, db, row, attrnames, sql):
        r = []
        table = self.q.run(db, sql)
        for i, e in enumerate(self.es):
            v = e.run(db, row, attrnames, sql)
            r.append(v)
        b = sql.doIn(r, table.rows, db, row, attrnames, sql)
        return b

    def typecheck(self, dbt, tablet, sql):
        tt = self.q.typecheck(dbt, sql)
        ex_tt = []
        global freshindex
        freshindex += 1
        for i, tbt in enumerate(tt.nametypes):
            oldname = tbt.name
            # newname = f"{'N'}{freshindex}{'.freshcol'}{i}"
            newname = f"{'N'}{freshindex}{'.'}{oldname}"
            tbt.name = newname
            ex_tt.append(tbt)

        tempt_tablet = tablet
        tempt_tablet.nametypes += ex_tt

        for i, e in enumerate(self.es):
            ee = Eq(e, NName(ex_tt[i].name))
            ee.typecheck(dbt, tempt_tablet, sql)
        return sql.resTypeEq()


    def trans(self, dbt, tablet, sql):
        q = self.q.trans(dbt, sql)
        tt2 = self.q.typecheck(dbt, sql)
        ex_tt = []
        global freshindex
        freshindex += 1
        cols = []
        for i, tbt in enumerate(tt2.nametypes):
            oldname = tbt.name
            newname = f"{'N'}{freshindex}{'.'}{oldname}"
            tbt.name = newname
            ex_tt.append(tbt)
            col = Alias(NName(oldname), newname)
            cols.append(col)

        tempt_tablet = tablet
        tempt_tablet.nametypes += ex_tt
        r_eqs =[]

        for i, e in enumerate(self.es):
            ee = Eq(e, NName(ex_tt[i].name))
            r_e = ee.trans(dbt, tempt_tablet, sql)
            r_eqs.append(r_e)

        lft_exps = []
        rgt_exps = []
        for i, eq in enumerate(r_eqs):
            lft_exps.append(eq.e1)
            rgt_exps.append(eq.e2)

        lft = lft_exps
        rgt1 = Proj(Beta(cols), q)
        rgt2 = []

        for i, c in enumerate(cols):
            rgt2.append(Alias((rgt_exps[i]), c.name))

        rgt = Proj(Beta(rgt2), rgt1)
        return Ins(lft, rgt)




