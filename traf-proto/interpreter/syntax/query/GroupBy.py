"""GroupBy query - GROUP BY clause"""

from interpreter.syntax.query.Query import Query
from interpreter.syntax.Beta import Beta
from interpreter.syntax.type.RelationType import RelationType


class GroupBy(Query):
    """
    GROUP BY query: groups rows by specified expressions and computes aggregates.
    
    Handles queries like:
        SELECT name, COUNT(*) FROM table GROUP BY name
    """
    
    def __init__(self, beta: Beta, grouping_exprs, query: Query, having_cond=None):
        """
        Initialize GroupBy query.
        
        Args:
            beta: Beta object with projections (may include aggregates and grouping columns)
            grouping_exprs: List of expressions to group by
            query: Underlying Query to group
            having_cond: Optional HAVING condition to filter groups
        """
        super().__init__()
        self.beta = beta
        self.grouping_exprs = grouping_exprs
        self.query = query
        self.having_cond = having_cond
    
    def __str__(self):
        grouping_str = ", ".join(str(e) for e in self.grouping_exprs)
        having_str = f" having {self.having_cond}" if self.having_cond else ""
        return f"(project {str(self.beta)} from {str(self.query)} group by {grouping_str}{having_str})"
    
    def __eq__(self, other):
        if not isinstance(other, GroupBy):
            return False
        return (self.beta == other.beta and 
                self.grouping_exprs == other.grouping_exprs and 
                self.query == other.query and
                self.having_cond == other.having_cond)
    
    def run(self, db, sql):
        """
        Execute the GROUP BY query.
        
        This is a placeholder - actual implementation will be in Phase 4.
        """
        # Placeholder implementation
        # Will be fully implemented in Phase 4 (Runtime Layer)
        raise NotImplementedError("GroupBy.run will be implemented in Phase 4")
    
    def typecheck(self, dbt, sql):
        """
        Type check the GROUP BY query.
        
        Validates that:
        1. The underlying query type checks
        2. All grouping expressions type check
        3. All non-aggregate expressions in beta are in grouping_exprs
        4. All aggregate expressions type check correctly
        """
        # Type check the underlying query
        tbt1 = self.query.typecheck(dbt, sql)
        tbt2 = RelationType(sql.removeUnk(tbt1.nametypes))
        
        # Type check all grouping expressions
        for expr in self.grouping_exprs:
            expr.typecheck(dbt, tbt2, sql)
        
        # Type check the beta (projection)
        # This will validate that aggregates type check and return appropriate types
        tbt3 = self.beta.typecheck(dbt, tbt2, sql)
        
        # TODO: Add validation that non-aggregate columns in beta are in grouping_exprs
        # This will be refined in Phase 5 (Typechecker Layer)
        
        return tbt3
    
    def get_col_names(self):
        """Get the output column names from beta."""
        return self.beta.get_col_names()
    
    def get_expressions(self):
        """Get the projection expressions from beta."""
        return self.beta.expressions()
    
    def update_expressions(self, es):
        """Update the projection expressions in beta."""
        for i, e in enumerate(es):
            self.beta.aliases[i].e = e
    
    def trans(self, dbt, sql):
        """
        Transform the GROUP BY expression (for query transformation/optimization).
        """
        # Transform the underlying query
        qq = self.query.trans(dbt, sql)
        
        # Get the type of the underlying query for transformation context
        tbt1 = self.query.typecheck(dbt, sql)
        tbt2 = RelationType(sql.removeUnk(tbt1.nametypes))
        
        # Transform grouping expressions
        transformed_grouping_exprs = [expr.trans(dbt, tbt2, sql) for expr in self.grouping_exprs]
        
        # Transform beta
        beta2 = self.beta.trans(dbt, tbt2, sql)
        
        # Transform HAVING condition if present
        transformed_having_cond = None
        if self.having_cond is not None:
            transformed_having_cond = self.having_cond.trans(dbt, tbt2, sql)
        
        return GroupBy(beta2, transformed_grouping_exprs, qq, transformed_having_cond)
    
    def getBeta(self):
        """Get the beta aliases (for set operations compatibility)."""
        return self.beta.aliases
