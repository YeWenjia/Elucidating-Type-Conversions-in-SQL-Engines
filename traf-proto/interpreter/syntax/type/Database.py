"""
Database type - represents a collection of tables

A Database is essentially a dictionary mapping table names to Table objects.
Example:
    db = Database({
        "TA": Table(["name", "height", "age"], rows_ta),
        "TB": Table(["realage", "fullname", "fullheight"], rows_tb),
    })
"""

from typing import Dict, List, Optional
from interpreter.syntax.Table import Table


class Database:
    """Represents a database as a collection of named tables"""
    
    def __init__(self, tables: Dict[str, Table]):
        """
        Initialize a database with a dictionary of tables.
        
        Args:
            tables: Dictionary mapping table names to Table objects
        """
        self.tables = tables
    
    def get_table(self, name: str) -> Optional[Table]:
        """
        Get a table by name (case-insensitive).
        
        Args:
            name: Name of the table
            
        Returns:
            Table object if found, None otherwise
        """
        # Try exact match first
        if name in self.tables:
            return self.tables[name]
        
        # Try case-insensitive match
        name_lower = name.lower()
        for table_name, table in self.tables.items():
            if table_name.lower() == name_lower:
                return table
        
        return None
    
    def get_table_names(self) -> List[str]:
        """
        Get all table names in the database.
        
        Returns:
            List of table names
        """
        return list(self.tables.keys())
    
    def has_table(self, name: str) -> bool:
        """
        Check if a table exists (case-insensitive).
        
        Args:
            name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        return self.get_table(name) is not None
    
    def add_table(self, name: str, table: Table):
        """
        Add a table to the database.
        
        Args:
            name: Name of the table
            table: Table object
        """
        self.tables[name] = table
    
    def remove_table(self, name: str) -> bool:
        """
        Remove a table from the database.
        
        Args:
            name: Name of the table
            
        Returns:
            True if table was removed, False if not found
        """
        if name in self.tables:
            del self.tables[name]
            return True
        return False
    
    def __getitem__(self, name: str) -> Table:
        """
        Access a table using dictionary syntax: db["table_name"]
        
        Args:
            name: Name of the table
            
        Returns:
            Table object
            
        Raises:
            KeyError: If table not found
        """
        table = self.get_table(name)
        if table is None:
            raise KeyError(f"Table '{name}' not found in database")
        return table
    
    def __setitem__(self, name: str, table: Table):
        """
        Set a table using dictionary syntax: db["table_name"] = table
        
        Args:
            name: Name of the table
            table: Table object
        """
        self.tables[name] = table
    
    def __contains__(self, name: str) -> bool:
        """
        Check if table exists using 'in' operator: "table_name" in db
        
        Args:
            name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        return self.has_table(name)
    
    def __len__(self) -> int:
        """
        Get number of tables in the database.
        
        Returns:
            Number of tables
        """
        return len(self.tables)
    
    def __str__(self) -> str:
        """
        String representation of the database.
        
        Returns:
            String showing all tables and their schemas
        """
        lines = [f"Database with {len(self.tables)} tables:"]
        for name, table in self.tables.items():
            lines.append(f"\n{name}:")
            lines.append(f"  Columns: {', '.join(table.cols)}")
            lines.append(f"  Rows: {len(table.rows)}")
        return '\n'.join(lines)
    
    def __repr__(self) -> str:
        """
        Detailed representation of the database.
        
        Returns:
            String showing constructor call
        """
        return f"Database(tables={{{', '.join(repr(k) for k in self.tables.keys())}}})"
    
    def __eq__(self, other) -> bool:
        """
        Check if two databases are equal.
        
        Args:
            other: Another Database object
            
        Returns:
            True if databases have same tables with same data
        """
        if not isinstance(other, Database):
            return False
        
        if len(self.tables) != len(other.tables):
            return False
        
        for name, table in self.tables.items():
            other_table = other.get_table(name)
            if other_table is None or table != other_table:
                return False
        
        return True
    
    def __iter__(self):
        """
        Iterate over table names (for dict-like interface).
        Allows: for table_name in db
        """
        return iter(self.tables)
    
    def keys(self):
        """Get table names (for dict-like interface)"""
        return self.tables.keys()
    
    def values(self):
        """Get tables (for dict-like interface)"""
        return self.tables.values()
    
    def items(self):
        """Get (name, table) pairs (for dict-like interface)"""
        return self.tables.items()
