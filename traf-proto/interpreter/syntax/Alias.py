from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.expression.BValue import BType


class Alias:
    """Alias for an expression in projection"""
    
    def __init__(self, e, name: str, internal_name: str = None):
        self.e = e
        self.name = name  # Display name (may be duplicated)
        self.internal_name = internal_name if internal_name is not None else name  # Unique internal name

    def __str__(self):
        return str(self.e) + " as " + str(self.name)

    def __eq__(self, other):
        if isinstance(other, Alias):
            return self.e == other.e and self.name == other.name
        return False

    def typecheck(self, dbt, tablet, sql):
        t = self.e.typecheck(dbt, tablet, sql)
        if t != BType():
            return RelationType([NameType(self.name, t)])
        else:
            raise Exception("Type checking fails!")

    def get_col_names(self):
        return [self.name]
    
    def trans(self, dbt, tablet, sql):
        ee = self.e.trans(dbt, tablet, sql)
        return Alias(ee, self.name, self.internal_name)
