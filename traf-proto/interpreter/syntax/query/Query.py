"""Base Query class for all SQL query AST nodes"""


class Query:
    """Abstract base class for all query nodes in the AST"""


    def typecheck(self, dbt, sql):
        """Type check the query and return RelationType"""
        pass

    def get_col_names(self):
        """Get the output column names"""
        pass

    def trans(self, dbt, sql):
        """Transform/optimize the query"""
        pass
    
    def getBeta(self):
        """Get Beta aliases (for set operations compatibility)"""
        raise Exception("Proj expected")
