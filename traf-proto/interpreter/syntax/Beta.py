from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.expression.BValue import BType


class Beta:
    """Beta for projection - wraps a list of Alias objects"""
    
    def __init__(self, aliases):
        # Rename duplicate display names with #N suffix to make internal names unique
        self.aliases = self._make_internal_names_unique(aliases)
    
    def _make_internal_names_unique(self, aliases):
        """Process aliases to ensure internal names are unique by adding #N suffix to duplicates"""
        from interpreter.syntax.Alias import Alias
        
        name_counts = {}
        result = []
        
        for alias in aliases:
            display_name = alias.name
            
            if display_name in name_counts:
                # This is a duplicate - add #N suffix to internal name
                count = name_counts[display_name]
                internal_name = f"{display_name}#{count}"
                name_counts[display_name] += 1
                # Create new Alias with unique internal name
                result.append(Alias(alias.e, display_name, internal_name))
            else:
                # First occurrence - use display name as internal name
                name_counts[display_name] = 1
                result.append(alias)
        
        return result

    def __str__(self):
        return ",".join(map(lambda a: str(a.e) + " as " + str(a.name), self.aliases))

    def __eq__(self, other):
        if isinstance(other, Beta):
            return self.aliases == other.aliases
        return False

    def expressions(self):
        return list(map(lambda a: a.e, self.aliases))

    def names(self):
        """Return internal names (unique) for lookups"""
        return list(map(lambda a: a.internal_name, self.aliases))

    def typecheck(self, dbt, tablet, sql):
        res = []
        # print(self.aliases)
        for aliase in self.aliases:
            # print(aliase.e.typecheck(tablet, sql))
            # Use internal_name for the NameType to ensure uniqueness
            res += [(NameType(aliase.internal_name, aliase.e.typecheck(dbt, tablet, sql)))]
            # print(aliase.e) # here
            # print(res)
            # print(NameType(aliase.name, aliase.e.typecheck(tablet, sql)))
            # print(aliase.e.typecheck(tablet, sql))

        # print(TableType(res))
        return RelationType(res)

    def get_col_names(self):
        """Return internal names (unique) for creating references"""
        return list(map(lambda a: a.internal_name, self.aliases))
    
    def trans(self, dbt, tablet, sql):
        return Beta(list(map(lambda a: a.trans(dbt, tablet, sql), self.aliases)))

    def getLastE(self):
        if self.aliases[-1]:
            return self.aliases[-1].e
        else:
            raise Exception("list of aliases is empty")

    def getLastName(self):
        if self.aliases[-1]:
            return self.aliases[-1].name
        else:
            raise Exception("list of aliases is empty")
