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
        #
        if self.v == None:
            self.isnull = True
        else:
            self.isnull = False
        self.isnull_not_null = False

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
        if self.v == None:
            return Nullv(None)
        elif type(self.v) == float:
            return Real(self.v, self.use_decimal)
        elif type(self.v) == int:
            return Natural(self.v)
        elif type(self.v) == str:
            return SString(self.v)
        elif type(self.v) == bool:
            return Boolean(self.v)
        elif type(self.v) == Decimal:
            return Real(self.v, self.use_decimal)



class Real(BValue):
    def __str__(self):
        return str(self.v)
    def value_or_not(self):
        return True

class Natural(BValue):
    def __str__(self):
        return str(self.v)
    def value_or_not(self):
        return True


class SString(BValue):
    def __str__(self):
        return str(self.v)
    def value_or_not(self):
        return True



class Boolean(BExpr, BValue):
    def __str__(self):
        return str(self.v)
    def value_or_not(self):
        return True


class Nullv(BValue):
    def __str__(self):
        return "NULL"
    def value_or_not(self):
        return True
