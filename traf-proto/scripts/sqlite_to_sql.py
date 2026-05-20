#!/usr/bin/env python3
"""
Convert SQLite db.sqlite files to db.sql with lowercase tables/columns.

Usage:
    # Single folder
    python scripts/sqlite_to_sql.py benchmarks/spider/allergy_1/tables
    
    # Multiple folders
    python scripts/sqlite_to_sql.py benchmarks/spider/*/tables
    
    # All Spider folders with db.sqlite
    python scripts/sqlite_to_sql.py benchmarks/spider/*/tables --auto
"""

import sqlite3
import sys
import re
from pathlib import Path
import argparse

# SQL reserved keywords that need to be renamed
SQL_RESERVED_KEYWORDS = {
    'rank', 'order', 'group', 'user', 'select', 'from', 'where', 'having',
    'limit', 'offset', 'union', 'intersect', 'except', 'join', 'left', 'right',
    'inner', 'outer', 'cross', 'on', 'using', 'as', 'distinct', 'all', 'and',
    'or', 'not', 'in', 'between', 'like', 'is', 'null', 'case', 'when', 'then',
    'else', 'end', 'exists', 'by', 'desc', 'asc', 'table', 'column', 'index',
    'key', 'primary', 'foreign', 'references', 'constraint', 'unique', 'check',
    'default', 'auto_increment', 'value', 'values', 'into', 'insert', 'update',
    'delete', 'create', 'drop', 'alter', 'truncate', 'database', 'schema',
    'view', 'trigger', 'procedure', 'function', 'grant', 'revoke', 'commit',
    'rollback', 'transaction', 'begin', 'end', 'if', 'for', 'while', 'loop',
    'return', 'set', 'declare', 'cursor', 'fetch', 'open', 'close'
}

def rename_if_reserved(column_name):
    """Add _col suffix to column names that are SQL reserved keywords."""
    lower_name = column_name.lower()
    if lower_name in SQL_RESERVED_KEYWORDS:
        return f'{lower_name}_col'
    return lower_name


def convert_sqlite_type_to_postgres(type_str):
    """Convert SQLite data type to PostgreSQL-compatible type."""
    if not type_str:
        return type_str
    
    type_upper = type_str.upper().strip()
    
    # Fix malformed types like "CHARACTER VARCHAR(3)" -> "VARCHAR(3)"
    type_upper = re.sub(r'CHARACTER\s+VARCHAR\s*\((\d+)\)', r'VARCHAR(\1)', type_upper, flags=re.IGNORECASE)
    type_str = re.sub(r'CHARACTER\s+VARCHAR\s*\((\d+)\)', r'VARCHAR(\1)', type_str, flags=re.IGNORECASE)
    
    # Map SQLite types to PostgreSQL types
    type_mapping = {
        'DATETIME': 'timestamp',
        'BOOL': 'boolean',
        'BOOLEAN': 'boolean',
        'BIT': 'integer',  # BIT in SQLite is really just 0/1, use INTEGER
    }
    
    # Check exact matches first (for base types without parameters)
    if type_upper in type_mapping:
        return type_mapping[type_upper]
    
    # Check prefixes for parameterized types like DATETIME(6)
    for sqlite_type, postgres_type in type_mapping.items():
        # Use regex to match whole word followed by optional parentheses
        pattern = r'\b' + re.escape(sqlite_type) + r'(\(|$)'
        if re.match(pattern, type_upper):
            # Replace the type but keep any parameters
            remainder = type_upper[len(sqlite_type):]
            return postgres_type + remainder.lower()
    
    # Convert CHAR(n) to VARCHAR(255) - SQLite doesn't enforce length
    # Use VARCHAR(255) to avoid truncation errors since SQLite data may exceed declared lengths
    char_pattern = r'\bCHAR\s*\([^)]*\)'
    if re.search(char_pattern, type_upper):
        return 'VARCHAR(255)'
    
    # Convert VARCHAR(n) where n < 255 to VARCHAR(255) for safety
    varchar_match = re.search(r'\bVARCHAR\s*\((\d+)\)', type_upper, re.IGNORECASE)
    if varchar_match:
        length = int(varchar_match.group(1))
        if length < 255:
            return 'VARCHAR(255)'
        # Keep larger lengths as-is
        return type_str
    
    return type_str


def strip_sql_comments(sql_text):
    """
    Remove SQL comments from the text.
    Handles both -- single-line comments and /* block comments */.
    """
    # Remove block comments /* ... */
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
    
    # Remove single-line comments --
    # Be careful to preserve strings that might contain --
    lines = sql_text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Simple approach: remove everything after -- that's not inside quotes
        # This is a simplified version; full SQL parsing would be complex
        comment_pos = line.find('--')
        if comment_pos >= 0:
            # Check if -- is inside a string literal (very basic check)
            # Count single quotes before the --
            before_comment = line[:comment_pos]
            single_quote_count = before_comment.count("'") - before_comment.count("\\'")
            # If even number of quotes, we're outside a string
            if single_quote_count % 2 == 0:
                line = line[:comment_pos]
        cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines)


def remove_backticks(sql_text):
    """
    Remove MySQL/SQLite backtick quotes from identifiers.
    Backticks are not valid in PostgreSQL.
    """
    # Remove backticks from identifiers, but be careful with string literals
    # Replace backticks with nothing (unquoted) for lowercase identifiers
    # or double quotes for mixed-case identifiers
    
    # Simple approach: replace all backticks with double quotes first,
    # then remove quotes around lowercase-only identifiers
    sql_text = sql_text.replace('`', '"')
    
    return sql_text


def sanitize_value_for_column(value, col_type):
    """
    Sanitize values for insertion, handling SQLite quirks.
    
    SQLite allows invalid data in columns:
    - Integer columns may contain strings like '94040-1724' -> extract leading digits
    - 'nil' strings -> NULL
    - Empty strings '' -> NULL (for numeric types)
    
    Args:
        value: The value to sanitize
        col_type: The column type (e.g., 'INTEGER', 'TEXT', 'VARCHAR')
    
    Returns:
        Sanitized value or None if should be NULL
    """
    # Handle None
    if value is None:
        return None
    
    # Check if column is numeric
    col_type_upper = col_type.upper().strip() if col_type else ''
    numeric_types = ['INTEGER', 'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT', 'DOUBLE', 'INT']
    is_numeric = any(col_type_upper.startswith(t) for t in numeric_types)
    
    # Handle string values
    if isinstance(value, str):
        # Convert 'nil' to NULL
        if value.lower() == 'nil':
            return None
        
        # Convert empty strings to NULL for numeric columns
        if is_numeric and value == '':
            return None
        
        # For numeric columns with string values like '94040-1724', extract leading integer
        if is_numeric and value:
            # Extract leading integer part (handles cases like '94040-1724')
            match = re.match(r'^(-?\d+)', value)
            if match:
                return int(match.group(1))
            # If no leading digits found and it's numeric column, convert to NULL
            return None
    
    # Return value as-is for other cases
    return value


def lowercase_identifiers(sql_line):
    """Convert table and column names to lowercase in SQL statements."""
    
    # Lowercase CREATE TABLE statements
    sql_line = re.sub(
        r'CREATE TABLE\s+([A-Za-z_][A-Za-z0-9_]*)',
        lambda m: f'CREATE TABLE {m.group(1).lower()}',
        sql_line,
        flags=re.IGNORECASE
    )
    
    # Lowercase column definitions (between parentheses in CREATE TABLE)
    # Handle PRIMARY KEY, FOREIGN KEY, REFERENCES specially
    def lowercase_column_name(match):
        col_def = match.group(1)
        # Don't lowercase SQL keywords
        keywords = ['PRIMARY KEY', 'FOREIGN KEY', 'REFERENCES', 'VARCHAR', 'INTEGER', 
                    'REAL', 'TEXT', 'BLOB', 'NULL', 'NOT NULL', 'DEFAULT', 
                    'AUTOINCREMENT', 'UNIQUE', 'CHECK']
        
        # Split by spaces and lowercase only the first word (column name)
        parts = col_def.strip().split(None, 1)
        if parts:
            parts[0] = parts[0].lower()
        return ' '.join(parts)
    
    # Process column definitions line by line within CREATE TABLE
    if 'CREATE TABLE' in sql_line.upper():
        # Extract table content between parentheses
        match = re.search(r'CREATE TABLE\s+\w+\s*\((.*)\);?', sql_line, re.IGNORECASE | re.DOTALL)
        if match:
            table_content = match.group(1)
            lines = table_content.split(',')
            new_lines = []
            
            for line in lines:
                line = line.strip()
                if line.upper().startswith('FOREIGN KEY'):
                    # Handle FOREIGN KEY(column) REFERENCES table(column)
                    line = re.sub(r'FOREIGN KEY\s*\(([^)]+)\)', 
                                  lambda m: f'FOREIGN KEY({rename_if_reserved(m.group(1).strip())})', 
                                  line, flags=re.IGNORECASE)
                    line = re.sub(r'REFERENCES\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]+)\)',
                                  lambda m: f'REFERENCES {m.group(1).lower()}({rename_if_reserved(m.group(2).strip())})',
                                  line, flags=re.IGNORECASE)
                elif line.upper().startswith('PRIMARY KEY'):
                    # Handle PRIMARY KEY(column1, column2, ...)
                    # Also handle: primary KEY ("Column_Name")
                    def lowercase_pk_cols(match):
                        cols = match.group(1).split(',')
                        # Remove quotes and whitespace, lowercase, then format
                        lowercased_cols = [rename_if_reserved(col.strip().strip('"')) for col in cols]
                        return f'primary KEY ({", ".join(lowercased_cols)})'
                    
                    line = re.sub(r'PRIMARY\s+KEY\s*\(([^)]+)\)', lowercase_pk_cols, line, flags=re.IGNORECASE)
                else:
                    # Regular column definition
                    # Check if it contains PRIMARY KEY constraint inline (e.g., "id" int PRIMARY KEY)
                    if re.search(r'\bPRIMARY\s+KEY\b', line, re.IGNORECASE):
                        # Just lowercase the column name part (first word)
                        parts = line.split(None, 1)
                        if parts:
                            parts[0] = rename_if_reserved(parts[0])
                            line = ' '.join(parts) if len(parts) > 1 else parts[0]
                    else:
                        # Regular column definition
                        parts = line.split(None, 1)
                        if parts:
                            parts[0] = rename_if_reserved(parts[0])
                            line = ' '.join(parts) if len(parts) > 1 else parts[0]
                
                new_lines.append(line)
            
            # Reconstruct the CREATE TABLE statement
            table_name_match = re.search(r'CREATE TABLE\s+(\w+)', sql_line, re.IGNORECASE)
            if table_name_match:
                table_name = table_name_match.group(1).lower()
                sql_line = f'CREATE TABLE {table_name} (\n       ' + ',\n       '.join(new_lines) + '\n);'
    
    # Lowercase INSERT INTO statements
    sql_line = re.sub(
        r'INSERT INTO\s+([A-Za-z_][A-Za-z0-9_]*)',
        lambda m: f'INSERT INTO {m.group(1).lower()}',
        sql_line,
        flags=re.IGNORECASE
    )
    
    # Lowercase column names in INSERT statements
    sql_line = re.sub(
        r'INSERT INTO\s+(\w+)\s+VALUES',
        lambda m: f'INSERT INTO {m.group(1).lower()} VALUES',
        sql_line,
        flags=re.IGNORECASE
    )
    
    return sql_line


def export_sqlite_to_sql(sqlite_path, output_path=None):
    """
    Export SQLite database to SQL file with lowercase identifiers.
    
    Args:
        sqlite_path: Path to db.sqlite file
        output_path: Path to output db.sql file (default: same directory)
    """
    sqlite_path = Path(sqlite_path)
    
    if not sqlite_path.exists():
        print(f"ERROR: {sqlite_path} does not exist")
        return False
    
    if output_path is None:
        output_path = sqlite_path.parent / 'db.sql'
    else:
        output_path = Path(output_path)
    
    print(f"Processing: {sqlite_path}")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(str(sqlite_path))
        
        # Get schema and data
        sql_lines = []
        foreign_keys = []  # Store foreign key constraints to add later
        
        # Start transaction
        sql_lines.append('BEGIN;')
        sql_lines.append('')
        
        # Get all tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get CREATE TABLE statement
            cursor = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            create_stmt = cursor.fetchone()[0]
            
            # Strip comments to avoid issues with multi-line comments
            create_stmt = strip_sql_comments(create_stmt)
            
            # Remove backticks (MySQL/SQLite quotes not valid in PostgreSQL)
            create_stmt = remove_backticks(create_stmt)
            
            # Parse the CREATE TABLE to extract columns and foreign keys
            # Extract the content between parentheses
            match = re.search(r'CREATE TABLE\s+[^\(]+\((.*)\)', create_stmt, re.DOTALL | re.IGNORECASE)
            if not match:
                print(f"WARNING: Could not parse CREATE TABLE for {table}")
                continue
                
            table_content = match.group(1)
            
            # Split by commas, but be careful with nested parentheses (e.g., VARCHAR(20))
            # Simple approach: split by comma followed by newline/spaces and column/FOREIGN/PRIMARY keywords
            lines = []
            current_line = ""
            paren_count = 0
            
            for char in table_content:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                elif char == ',' and paren_count == 0:
                    lines.append(current_line.strip())
                    current_line = ""
                    continue
                current_line += char
            
            if current_line.strip():
                lines.append(current_line.strip())
            
            # Separate regular columns from foreign keys
            columns = []
            for line in lines:
                line_upper = line.strip().upper()
                if line_upper.startswith('FOREIGN KEY') or line_upper.startswith('CONSTRAINT'):
                    # Skip FOREIGN KEY and CONSTRAINT clauses - we don't add them to PostgreSQL
                    # (Spider data often has FK violations, and constraints are already in lowercase_identifiers)
                    continue
                elif line_upper.startswith('PRIMARY KEY') and '(' in line:
                    # Table-level PRIMARY KEY constraint
                    columns.append(line)
                else:
                    # Regular column definition
                    columns.append(line)
            
            # Rebuild CREATE TABLE with lowercase names
            table_lower = table.lower()
            lowercased_columns = []
            
            for col in columns:
                # Handle PRIMARY KEY constraint specially
                if col.strip().upper().startswith('PRIMARY KEY'):
                    # Lowercase column names inside PRIMARY KEY(...) constraint
                    def lowercase_pk_cols(match):
                        cols = match.group(1).split(',')
                        # Remove quotes and whitespace, rename if reserved
                        lowercased_cols = [rename_if_reserved(c.strip().strip('"').strip("'").strip('`')) for c in cols]
                        return f'primary KEY ({", ".join(lowercased_cols)})'
                    
                    col = re.sub(r'PRIMARY\s+KEY\s*\(([^)]+)\)', lowercase_pk_cols, col, flags=re.IGNORECASE)
                    lowercased_columns.append(col)
                    continue
                    
                # Lowercase column name (first word) but keep types as-is
                parts = col.strip().split(None, 1)
                if parts:
                    # Remove any quotes from column name and rename if reserved
                    parts[0] = rename_if_reserved(parts[0].strip('"').strip("'").strip('`'))
                    
                    # Convert data types to PostgreSQL-compatible ones
                    if len(parts) > 1:
                        # Parse the type from the column definition
                        # Format: "column_name TYPE constraints..."
                        type_and_constraints = parts[1]
                        
                        # Extract the type which might have parentheses but stops at constraint keywords
                        # e.g., "VARCHAR(255) NOT NULL", "datetime DEFAULT", "INTEGER NOT NULL"
                        # Type pattern: word(s) optionally followed by parentheses, but no constraint keywords
                        type_match = re.match(r'([A-Za-z_][A-Za-z0-9_]*(?:\([^)]*\))?)', type_and_constraints)
                        if type_match:
                            original_type = type_match.group(1).strip()
                            postgres_type = convert_sqlite_type_to_postgres(original_type)
                            
                            # Replace the type in the definition
                            if postgres_type != original_type:
                                type_and_constraints = type_and_constraints.replace(original_type, postgres_type, 1)
                            
                            parts[1] = type_and_constraints
                    
                    lowercased_col = ' '.join(parts) if len(parts) > 1 else parts[0]
                    lowercased_columns.append(lowercased_col)
            
            create_stmt = f"CREATE TABLE {table_lower} (\n       " + ',\n       '.join(lowercased_columns) + "\n);"
            sql_lines.append(create_stmt)
            sql_lines.append('')
            
            # Extract column types for proper NULL handling
            # Get column info from SQLite
            cursor = conn.execute(f'PRAGMA table_info("{table}")')
            column_info = cursor.fetchall()
            # column_info is list of (cid, name, type, notnull, dflt_value, pk)
            column_types = [col[2].upper() for col in column_info]
            
            def is_numeric_type(type_str):
                """Check if a type is numeric (should reject empty strings)"""
                if not type_str:
                    return False
                type_upper = type_str.upper().strip()
                numeric_types = ['INTEGER', 'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT', 'DOUBLE']
                return any(type_upper.startswith(t) for t in numeric_types)
            
            # Get all data from table
            cursor = conn.execute(f'SELECT * FROM "{table}"')
            rows = cursor.fetchall()
            
            if rows:
                table_lower = table.lower()
                for row in rows:
                    # Format values
                    values = []
                    for idx, val in enumerate(row):
                        # Get column type
                        col_type = column_types[idx] if idx < len(column_types) else ''
                        
                        # Sanitize value (handles SQLite quirks: 'nil', '94040-1724', empty strings)
                        sanitized = sanitize_value_for_column(val, col_type)
                        
                        # Format the value for SQL
                        if sanitized is None:
                            values.append('NULL')
                        elif isinstance(sanitized, str):
                            # Escape single quotes in strings
                            escaped = sanitized.replace("'", "''")
                            values.append(f"'{escaped}'")
                        elif isinstance(sanitized, (int, float)):
                            values.append(str(sanitized))
                        else:
                            # Fallback for other types
                            values.append(f"'{sanitized}'")
                    
                    insert_stmt = f"INSERT INTO {table_lower} VALUES ({', '.join(values)});"
                    sql_lines.append(insert_stmt)
                
                sql_lines.append('')
        
        # Note: Foreign key constraints are NOT added because many Spider datasets
        # have data inconsistencies that would violate FK constraints.
        # SQLite doesn't enforce FKs by default, so the original data may be invalid.
        # Uncomment below if you want to add FKs (may cause errors with Spider data):
        # if foreign_keys:
        #     sql_lines.append('-- Add foreign key constraints')
        #     for i, fk in enumerate(foreign_keys):
        #         constraint_name = f"fk_{fk['table']}_{fk['column']}_{i}"
        #         alter_stmt = (
        #             f"ALTER TABLE {fk['table']} "
        #             f"ADD CONSTRAINT {constraint_name} "
        #             f"FOREIGN KEY ({fk['column']}) "
        #             f"REFERENCES {fk['ref_table']}({fk['ref_column']});"
        #         )
        #         sql_lines.append(alter_stmt)
        #     sql_lines.append('')
        
        # End transaction
        sql_lines.append('COMMIT;')
        
        conn.close()
        
        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_lines))
        
        print(f"✓ Created: {output_path}")
        return True
        
    except Exception as e:
        print(f"ERROR processing {sqlite_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_and_process_all(base_path):
    """Find all db.sqlite files and process them."""
    base_path = Path(base_path)
    
    # Find all db.sqlite files
    sqlite_files = list(base_path.glob('**/db.sqlite'))
    
    if not sqlite_files:
        print(f"No db.sqlite files found in {base_path}")
        return
    
    print(f"Found {len(sqlite_files)} db.sqlite files\n")
    
    success_count = 0
    for sqlite_path in sorted(sqlite_files):
        if export_sqlite_to_sql(sqlite_path):
            success_count += 1
        print()
    
    print(f"\nSummary: {success_count}/{len(sqlite_files)} files processed successfully")


def main():
    parser = argparse.ArgumentParser(
        description='Convert SQLite db.sqlite files to db.sql with lowercase identifiers'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        help='Paths to folders containing db.sqlite or to db.sqlite files directly'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-find all db.sqlite files in the given path'
    )
    parser.add_argument(
        '--base-path',
        default='benchmarks/spider',
        help='Base path for --auto mode (default: benchmarks/spider)'
    )
    
    args = parser.parse_args()
    
    if args.auto or not args.paths:
        # Auto mode: find all db.sqlite files
        base_path = args.base_path if not args.paths else args.paths[0]
        find_and_process_all(base_path)
    else:
        # Process specified paths
        for path_str in args.paths:
            path = Path(path_str)
            
            if path.is_file() and path.name == 'db.sqlite':
                export_sqlite_to_sql(path)
            elif path.is_dir():
                sqlite_path = path / 'db.sqlite'
                if sqlite_path.exists():
                    export_sqlite_to_sql(sqlite_path)
                else:
                    print(f"WARNING: {sqlite_path} does not exist")
            else:
                print(f"WARNING: {path} is not a valid path")


if __name__ == '__main__':
    main()
