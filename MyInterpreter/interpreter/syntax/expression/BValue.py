from interpreter.syntax.expression.Expression import Expr
from interpreter.syntax.expression.BExpr import BExpr
from interpreter.syntax.type.ValueType import *
from decimal import Decimal
from decimal import Decimal


class BValue(Expr):
    def __init__(self, v, use_decimal=True):
        self.use_decimal = use_decimal
        if type(v) == float and self.use_decimal:

            self.v = Decimal(str(v))
        else:
            self.v = v
        self.unknown = True

    def __eq__(self, other):
        return self.v == other.v

    def value_or_not(self):
        return True

    def erase(self):
        return self.v

    def run(self, db, row, attrnames, sql):
        return BValue(self.v, self.use_decimal)

    def __str__(self):
        return str(self.v)

    def trans(self, dbt, tablet, sql):
        pass

    def rawValueToObj(self):
        if type(self.v) == float:
            return Real(self.v, self.use_decimal)
        elif type(self.v) == int:
            return Natural(self.v)
        elif type(self.v) == str:
            return SString(self.v)
        elif type(self.v) == bool:
            return Boolean(self.v)
        elif type(self.v) == Decimal:
            return Real(self.v, self.use_decimal)

    # def cast(self, t, sql):
    #     v = BValue(self.rawValueToObj().cast(t, sql), self.use_decimal)
    #     v.unknown = t.tag == 'Unknown'
    #     return v
    #
    #     # if type(self.v) == float:
    #     #     if t.tag != 'Unknown':
    #     #         v = BValue(Real(self.v).cast(t, sql))
    #     #         v.unknown = False
    #     #         return v
    #     #     else:
    #     #         return BValue(Real(self.v).cast(t, sql))
    #     # elif type(self.v) == int:
    #     #     if t.tag != 'Unknown':
    #     #         v = BValue(Natural(self.v).cast(t, sql))
    #     #         v.unknown = False
    #     #         return v
    #     #     else:
    #     #         return BValue(Natural(self.v).cast(t, sql))
    #     # elif type(self.v) == str:
    #     #     if t.tag != 'Unknown':
    #     #         v = BValue(SString(self.v).cast(t, sql))
    #     #         v.unknown = False
    #     #         return v
    #     #     else:
    #     #         return BValue(SString(self.v).cast(t, sql))
    #     # elif type(self.v) == bool:
    #     #     if t.tag != 'Unknown':
    #     #         v = BValue(Boolean(self.v).cast(t, sql))
    #     #         v.unknown = False
    #     #         return v
    #     #     else:
    #     #         return BValue(Boolean(self.v).cast(t, sql))
    #
    # def upcast(self, t, sql):
    #     v = BValue(self.rawValueToObj().upcast(t, sql), self.use_decimal)
    #     v.unknown = t.tag == 'Unknown'
    #     return v


class Real(BValue):
    def value_or_not(self):
        return True

    # def typecheck(self, dbt, tablet, sql):
    #     if sql.tag == 'Sqlite':
    #         return UType()
    #     else:
    #         return RType()
    #
    # def cast(self, t, sql):
    #     return t.castFromReal(self.v, sql)
    #
    # # def icast(self, t, sql):
    # #     return t.icastFromReal(self.v, sql)
    #
    # def upcast(self, t, sql):
    #     if (t.tag == "Real"):
    #         return self.v
    #     else:
    #         raise Exception("conversion fails!")
    #
    # def trans(self, dbt, tablet, sql):
    #     return Real(self.v, self.use_decimal)


class Natural(BValue):
    def value_or_not(self):
        return True
    #
    # def typecheck(self, dbt, tablet, sql):
    #     if sql.tag == 'Sqlite':
    #         return UType()
    #     else:
    #         return ZType()
    #
    # def cast(self, t, sql):
    #     return t.castFromInt(self.v, sql)
    #
    # # def icast(self, t, sql):
    # #     return t.icastFromInt(self.v, sql)
    #
    # def upcast(self, t, sql):
    #     if t.tag == "Int":
    #         return self.v
    #     elif t.tag == "Real":
    #         return Decimal(str(self.v))
    #     else:
    #         raise Exception("conversion fails!")
    #
    # def trans(self, dbt, tablet, sql):
    #     return Natural(self.v)


class SString(BValue):
    def value_or_not(self):
        return True

    # def typecheck(self, dbt, tablet, sql):
    #     if sql.tag in ["Postgres", "Sqlite"]:
    #         return UType()
    #     else:
    #         return SType()
    #
    # def cast(self, t, sql):
    #     # refactor:
    #     return t.castFromString(self.v, sql)
    #
    # def icast(self, t, sql):
    #     # refactor:
    #     return t.icastFromString(self.v, sql)
    #
    # def upcast(self, t, sql):
    #     if t.tag == "String":
    #         return self.v
    #     if t.tag == "Unknown":
    #         return self.v
    #     elif t.tag == "Int":
    #         return sql.upcastSToInt(self.v)
    #     elif t.tag == "Real":
    #         try:
    #             return Decimal(self.v)
    #         except ValueError:
    #             raise Exception("cast fail!")
    #     else:
    #         raise Exception("cast fails")
    #
    # def trans(self, dbt, tablet, sql):
    #     return SString(self.v)


class Boolean(BExpr, BValue):
    def value_or_not(self):
        return True

    def typecheck(self, dbt, tablet, sql):
        if sql.tag == 'Sqlite':
            return UType()
        else:
            return BType()

    def cast(self, t, sql):
        return t.castFromBool(self.v, sql)

    def upcast(self, t, sql):
        if t.tag == "Bool":
            return self.v
        else:
            raise Exception("conversion fails")

    def trans(self, dbt, tablet, sql):
        return Boolean(self.v)
