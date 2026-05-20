# This is a pair N \mapsto \tau in the paper
from interpreter.syntax.type.ValueType import ValueType


class NameType:
    def __init__(self, name: str, type: ValueType):
        self.name = name
        self.type = type

    def __str__(self):
        return str(self.name) + ": " + str(self.type)

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type


# This is T in the paper
class RelationType:
    def __init__(self, nametypes: list[NameType]):
        self.nametypes = nametypes

    def __str__(self):
        return "[" + ",".join([str(x) for x in self.nametypes]) + "]"

    def __eq__(self, other):
        return self.nametypes == other.nametypes

    def getLast(self):
        return self.nametypes[-1]
    
    def getColNames(self) -> list[str]:
        return [nt.name for nt in self.nametypes]

    def getTypeByName(self, name):
        # SQL scoping: when the scope is built by concatenating outer-before-inner,
        # ambiguous unqualified lookups must resolve to the innermost scope
        # (last match), not the outermost. Outer-scope names should only be
        # visible as correlated references when the inner scope lacks them.
        exact = [nt for nt in self.nametypes if nt.name == name]
        if exact:
            return exact[-1].type

        # Qualified name (t.col) with no exact match: try stripping the prefix.
        if '.' in name:
            unqualified_name = name.split('.', 1)[1]
            stripped = [nt for nt in self.nametypes if nt.name == unqualified_name]
            if stripped:
                return stripped[-1].type

        # Unqualified name: match against qualified cols whose suffix matches,
        # plus any bare column with the same name.
        else:
            matches = []
            for nt in self.nametypes:
                if '.' in nt.name:
                    col_name = nt.name.split('.', 1)[1]
                    if col_name == name:
                        matches.append(nt)
                elif nt.name == name:
                    matches.append(nt)
            if matches:
                return matches[-1].type

        raise Exception(f"Column '{name}' not found in RelationType: {self}")

    def concat(self, other: 'RelationType') -> 'RelationType':
        """
        Concatenate this RelationType with another RelationType.
        
        The argument 'other' extends and/or replaces existing keys:
        - If a column name exists in both, the one from 'other' takes precedence
        - New columns from 'other' are added
        - Columns only in 'self' are preserved
        
        Args:
            other: RelationType to concatenate with this one
            
        Returns:
            New RelationType with merged nametypes
        """
        # Create a dictionary to track all columns by name
        # Start with columns from self
        merged = {}
        for nt in self.nametypes:
            merged[nt.name] = nt
        
        # Update/add columns from other (replacements happen here)
        for nt in other.nametypes:
            merged[nt.name] = nt
        
        # Return new RelationType preserving order:
        # First, columns from self (possibly replaced)
        # Then, new columns from other
        result_nametypes = []
        seen = set()
        
        # Add columns from self first (preserving order, with possible replacements)
        for nt in self.nametypes:
            result_nametypes.append(merged[nt.name])
            seen.add(nt.name)
        
        # Add new columns from other that weren't in self
        for nt in other.nametypes:
            if nt.name not in seen:
                result_nametypes.append(nt)
        
        return RelationType(result_nametypes)
