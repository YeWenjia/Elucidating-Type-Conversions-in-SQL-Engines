"""
Syntax module - backward compatibility imports

This file maintains backward compatibility by re-exporting all classes
that were previously defined in this file. The actual implementations
have been moved to separate files for better organization:

- utils.py: changeb() function
- Beta.py and Alias.py: Projection-related classes
- query/: All Query subclasses (Rel, Proj, Sel, Setop, Eps, OrderBy, Limit, GroupBy)
- Table.py: Table result class
"""

# Import type classes that were previously imported at top of this file
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.expression.BValue import *

# Import all components from their new locations
from interpreter.syntax.utils import changeb
from interpreter.syntax.Beta import Beta
from interpreter.syntax.Alias import Alias
from interpreter.syntax.Table import Table
from interpreter.syntax.query.Query import Query
from interpreter.syntax.query.Rel import Rel
from interpreter.syntax.query.Proj import Proj
from interpreter.syntax.query.Sel import Sel
from interpreter.syntax.query.Setop import Setop
from interpreter.syntax.query.Eps import Eps
from interpreter.syntax.query.OrderBy import OrderBy
from interpreter.syntax.query.Limit import Limit
from interpreter.syntax.query.GroupBy import GroupBy

# Export all for backward compatibility
__all__ = [
    'changeb',
    'Beta',
    'Alias',
    'Query',
    'Rel',
    'Proj',
    'Sel',
    'Setop',
    'Eps',
    'OrderBy',
    'Limit',
    'GroupBy',
    'Table',
    'RelationType',
    'NameType',
    # BValue types
    'BValue',
    'Real',
    'Natural',
    'SString',
    'Boolean',
    'Nullv',
]
