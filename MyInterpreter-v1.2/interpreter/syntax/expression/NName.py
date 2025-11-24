from interpreter.syntax.expression.Ascr import Ascr
from interpreter.syntax.expression.Expression import *

from interpreter.syntax.expression.BValue import *

import re

class NName(Expr):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.isnull_not_null = False


    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def run(self, db, row, attrnames, sql):
        # if self.name in attrnames:
        vc = row[attrnames.index(self.name)]
        # problem here
        # v.unknown = False
        return vc
    

    def typecheck(self, dbt, tablet, sql):
        # print(tablet.dic[self.name])
        # print(tablet.getTypeByName(self.name))
        # print(tablet)
        return tablet.getTypeByName(self.name)

    def trans(self, dbt, tablet, sql):
        return NName(self.name)