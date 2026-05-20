#!/usr/bin/env python3
"""
Script to normalize SQL queries in YAML files to be Postgres-friendly:
- Convert all table names to lowercase
- Convert all column names to lowercase
- Convert double-quoted string literals to single quotes
- Rename SQL reserved keywords used as column names by adding _col suffix
"""

import argparse
import re
import yaml
from pathlib import Path
from typing import List, Tuple

# SQL reserved keywords that are commonly used as column names and need renaming
# This is a subset focused on commonly problematic keywords
COLUMN_NAME_RESERVED_KEYWORDS = {
    'rank', 'order', 'group', 'user', 'key', 'value', 'index', 
    'table', 'column', 'default', 'check', 'constraint'
}


def _split_respecting_parens(s: str, delimiter: str = ',') -> List[str]:
    """Split a string by delimiter, but respect parenthesized groups."""
    parts = []
    current = []
    depth = 0
    for ch in s:
        if ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == delimiter and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append(''.join(current).strip())
    return [p for p in parts if p]


def _extract_column_name(expr: str) -> str:
    """
    Extract the base column name from a SELECT expression.
    Handles: 'col', 'table.col', 'col AS alias', 'table.col AS alias'.
    Returns the column name (without table qualifier), or empty string if it's an aggregate/complex expr.
    """
    agg_funcs = re.compile(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', re.IGNORECASE)
    if agg_funcs.search(expr):
        return ''

    # Strip alias: "expr AS alias" -> "expr"
    as_match = re.match(r'(.+?)\s+AS\s+\w+\s*$', expr, re.IGNORECASE)
    if as_match:
        expr = as_match.group(1).strip()

    # Handle qualified name: "table.col" -> "col" but keep full form for GROUP BY
    expr = expr.strip()
    # If it's a simple identifier or qualified identifier, return it
    if re.match(r'^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)?$', expr, re.IGNORECASE):
        return expr
    return ''


def _fix_group_by(sql: str) -> str:
    """
    Fix GROUP BY to include all non-aggregated SELECT columns.
    PostgreSQL requires every non-aggregated column in SELECT to appear in GROUP BY.
    """
    # Only process queries that have GROUP BY
    group_by_match = re.search(r'\bGROUP\s+BY\b', sql, re.IGNORECASE)
    if not group_by_match:
        return sql

    # Extract SELECT list (between SELECT [DISTINCT] and FROM)
    select_match = re.search(r'\bSELECT\s+(?:DISTINCT\s+)?(.*?)\bFROM\b', sql, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return sql

    select_list_str = select_match.group(1).strip()
    select_items = _split_respecting_parens(select_list_str)

    # Find non-aggregated columns in SELECT
    non_agg_columns = []
    for item in select_items:
        col = _extract_column_name(item)
        if col:
            non_agg_columns.append(col)

    if not non_agg_columns:
        return sql

    # Extract current GROUP BY columns
    # GROUP BY ... up to ORDER BY, HAVING, LIMIT, ), ;, or end of string
    gb_match = re.search(
        r'\bGROUP\s+BY\s+(.*?)(?:\s+(?:ORDER\s+BY|HAVING|LIMIT)\b|\)|;|$)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if not gb_match:
        return sql

    gb_str = gb_match.group(1).strip()
    gb_columns = [c.strip().lower() for c in _split_respecting_parens(gb_str)]

    # Find missing columns (compare case-insensitively)
    missing = []
    for col in non_agg_columns:
        # For comparison, normalize: "t1.name" matches "t1.name", "name" matches "name"
        col_lower = col.lower()
        # Also check if the unqualified name matches
        col_base = col_lower.split('.')[-1] if '.' in col_lower else col_lower
        found = False
        for gb_col in gb_columns:
            gb_base = gb_col.split('.')[-1] if '.' in gb_col else gb_col
            if col_lower == gb_col or col_base == gb_base:
                found = True
                break
        if not found:
            missing.append(col)

    if not missing:
        return sql

    # Append missing columns to GROUP BY
    new_gb = gb_str + ', ' + ', '.join(missing)
    sql = sql[:gb_match.start(1)] + new_gb + sql[gb_match.end(1):]

    return sql


def normalize_sql_for_postgres(sql: str) -> str:
    """
    Transform SQL query to be Postgres-friendly by:
    1. Converting identifiers (tables/columns) to lowercase
    2. Converting double-quoted strings to single quotes
    """
    
    # First, protect string literals by temporarily replacing them
    # Find all double-quoted strings and single-quoted strings
    string_literals = []
    
    def save_string_literal(match):
        """Save string literal and return placeholder"""
        string_literals.append(match.group(0))
        # Use a placeholder with no word characters to avoid regex matching
        return f"<<<{len(string_literals) - 1}>>>"
    
    # Save existing single-quoted strings first
    sql_protected = re.sub(r"'[^']*'", save_string_literal, sql)
    
    # Convert double-quoted strings to single quotes and save them
    def convert_double_quotes(match):
        """Convert double quotes to single quotes"""
        content = match.group(1)
        string_literals.append(f"'{content}'")
        return f"<<<{len(string_literals) - 1}>>>"
    
    sql_protected = re.sub(r'"([^"]*)"', convert_double_quotes, sql_protected)
    
    # Now lowercase all identifiers (anything that looks like a table/column name)
    # This includes: word characters, underscores, and dots (for qualified names)
    # But we need to be careful with SQL keywords
    
    # Convert identifiers to lowercase
    # Match words that are likely identifiers (contain underscore or are after FROM, JOIN, etc.)
    def lowercase_identifier(match):
        """Convert identifier to lowercase"""
        word = match.group(0)
        # Don't lowercase SQL keywords (keep them as-is in the original)
        sql_keywords = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'AND', 'OR', 'AS', 'ORDER', 
            'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'ASC', 'DESC', 'DISTINCT',
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
            'UNION', 'INTERSECT', 'EXCEPT', 'IN', 'NOT', 'NULL', 'LIKE', 'BETWEEN',
            'IS', 'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'ALL', 'ANY',
            'SOME', 'TRUE', 'FALSE'
        }
        if word.upper() in sql_keywords:
            return word  # Keep original case for keywords
        return word.lower()
    
    # Match words (identifiers) - including those with dots for qualified names
    sql_normalized = re.sub(r'\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\b', 
                           lowercase_identifier, sql_protected)
    
    # Rename reserved keywords when used as column names
    # We need to be careful to only rename in column contexts, not in SQL keyword contexts
    # Safe contexts: after SELECT (with comma or alias), after dot (qualified name), 
    # in WHERE/HAVING with =/</>... operators
    
    # Pattern 1: Qualified names (table.column)
    def rename_qualified_column(match):
        prefix = match.group(1)
        column = match.group(2)
        if column in COLUMN_NAME_RESERVED_KEYWORDS:
            return f'{prefix}.{column}_col'
        return match.group(0)
    
    sql_normalized = re.sub(r'(\b[a-z_][a-z0-9_]*)\.(rank|order|group|user|key|value|index|table|column|default|check|constraint)\b',
                           rename_qualified_column, sql_normalized)
    
    # Pattern 2: Column in SELECT list (after SELECT or comma, before comma/FROM/WHERE/etc)
    # Match: SELECT rank, or SELECT DISTINCT rank, or , rank
    sql_normalized = re.sub(r'(SELECT\s+(?:DISTINCT\s+)?)(rank|order|group|user|key|value|index|table|column|default|check|constraint)\b',
                           lambda m: f'{m.group(1)}{m.group(2)}_col', sql_normalized, flags=re.IGNORECASE)
    sql_normalized = re.sub(r'(,\s*)(rank|order|group|user|key|value|index|table|column|default|check|constraint)\b',
                           lambda m: f'{m.group(1)}{m.group(2)}_col', sql_normalized)
    
    # Pattern 3: Column in WHERE/HAVING clauses (with = or other operators)
    sql_normalized = re.sub(r'(WHERE\s+.*?)(rank|order|group|user|key|value|index|table|column|default|check|constraint)(\s*[=<>!])',
                           lambda m: f'{m.group(1)}{m.group(2)}_col{m.group(3)}', sql_normalized, flags=re.IGNORECASE)
    sql_normalized = re.sub(r'(HAVING\s+.*?)(rank|order|group|user|key|value|index|table|column|default|check|constraint)(\s*[=<>!])',
                           lambda m: f'{m.group(1)}{m.group(2)}_col{m.group(3)}', sql_normalized, flags=re.IGNORECASE)
    sql_normalized = re.sub(r'(AND\s+)(rank|order|group|user|key|value|index|table|column|default|check|constraint)(\s*[=<>!])',
                           lambda m: f'{m.group(1)}{m.group(2)}_col{m.group(3)}', sql_normalized, flags=re.IGNORECASE)
    
    # Pattern 4: Column in GROUP BY
    sql_normalized = re.sub(r'(GROUP\s+BY\s+)(rank|order|group|user|key|value|index|table|column|default|check|constraint)\b',
                           lambda m: f'{m.group(1)}{m.group(2)}_col', sql_normalized, flags=re.IGNORECASE)
    sql_normalized = re.sub(r'(GROUP\s+BY\s+[^,]+,\s*)(rank|order|group|user|key|value|index|table|column|default|check|constraint)\b',
                           lambda m: f'{m.group(1)}{m.group(2)}_col', sql_normalized, flags=re.IGNORECASE)
    
    # Pattern 5: Column in ORDER BY
    sql_normalized = re.sub(r'(ORDER\s+BY\s+)(rank|order|group|user|key|value|index|table|column|default|check|constraint)\b',
                           lambda m: f'{m.group(1)}{m.group(2)}_col', sql_normalized, flags=re.IGNORECASE)
    
    # Fix GROUP BY: ensure all non-aggregated SELECT columns are in GROUP BY
    sql_normalized = _fix_group_by(sql_normalized)

    # Restore string literals
    for i, literal in enumerate(string_literals):
        sql_normalized = sql_normalized.replace(f"<<<{i}>>>", literal)

    return sql_normalized


def process_yaml_file(yaml_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Process a single YAML file and normalize its SQL query.
    
    Returns:
        Tuple of (changed, message)
    """
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'sql' not in data:
            return False, "No SQL field found"
        
        original_sql = data['sql']
        normalized_sql = normalize_sql_for_postgres(original_sql)
        
        # Also update the 'columns' field if it exists and contains reserved keywords
        columns_changed = False
        if 'columns' in data and isinstance(data['columns'], list):
            new_columns = []
            for col in data['columns']:
                if isinstance(col, str) and col.lower() in COLUMN_NAME_RESERVED_KEYWORDS:
                    new_columns.append(f'{col.lower()}_col')
                    columns_changed = True
                else:
                    new_columns.append(col)
            if columns_changed:
                data['columns'] = new_columns
        
        if original_sql == normalized_sql and not columns_changed:
            return False, "No changes needed"
        
        if dry_run:
            return True, f"Would change:\n{original_sql}\n  ->\n{normalized_sql}"
        
        # If columns were changed, we need to rewrite the full YAML file
        if columns_changed:
            # Custom representer to force literal style for multiline strings
            class literal_str(str):
                pass
            
            def literal_presenter(dumper, data):
                if '\n' in data:
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|-')
                return dumper.represent_scalar('tag:yaml.org,2002:str', data)
            
            yaml.add_representer(literal_str, literal_presenter)
            data['sql'] = literal_str(normalized_sql)
            
            with open(yaml_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        else:
            # Only SQL changed, so just replace the SQL section to preserve formatting
            # Read the original file to preserve formatting
            with open(yaml_path, 'r') as f:
                original_content = f.read()
            
            # Find and replace just the SQL section
            # Look for "sql: |-" or "sql:" followed by the SQL content
            import re
            
            # Try to find the SQL block with |- style
            if 'sql: |-' in original_content or 'sql: |' in original_content:
                # Use regex to find and replace the SQL block
                # Match: sql: |- or sql: | followed by indented lines
                pattern = r'(sql: \|-?\n)((?:  .*\n)*)'
                
                def replace_sql(match):
                    prefix = match.group(1)
                    # Take the normalized SQL and indent it properly
                    indented_sql = '\n'.join('  ' + line if line else '' for line in normalized_sql.split('\n'))
                    return prefix + indented_sql + '\n'
                
                new_content = re.sub(pattern, replace_sql, original_content)
                
                with open(yaml_path, 'w') as f:
                    f.write(new_content)
            else:
                # Fallback: if format is different, use the old method but with literal style
                data['sql'] = normalized_sql
                
                # Custom representer to force literal style for multiline strings
                class literal_str(str):
                    pass
                
                def literal_presenter(dumper, data):
                    if '\n' in data:
                        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|-')
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
                
                yaml.add_representer(literal_str, literal_presenter)
                data['sql'] = literal_str(normalized_sql)
                
                with open(yaml_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        return True, "Updated"
    
    except Exception as e:
        return False, f"Error: {str(e)}"


def process_folder(folder_path: Path, dry_run: bool = False) -> None:
    """
    Process all YAML files in a folder.
    """
    yaml_files = sorted(folder_path.glob("*.yaml"))
    
    if not yaml_files:
        print(f"No YAML files found in {folder_path}")
        return
    
    print(f"Processing {len(yaml_files)} YAML files in {folder_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print("-" * 80)
    
    changed_count = 0
    for yaml_file in yaml_files:
        changed, message = process_yaml_file(yaml_file, dry_run)
        if changed:
            changed_count += 1
            print(f"✓ {yaml_file.name}: {message}")
        else:
            if dry_run and message != "No changes needed":
                print(f"  {yaml_file.name}: {message}")
    
    print("-" * 80)
    print(f"Summary: {changed_count}/{len(yaml_files)} files {'would be' if dry_run else 'were'} changed")
    
    # Delete CSV files from the tables subfolder
    tables_path = folder_path / "tables"
    if tables_path.exists():
        csv_files = list(tables_path.glob("*.csv"))
        if csv_files:
            print(f"\n{'Would delete' if dry_run else 'Deleting'} {len(csv_files)} CSV files from {tables_path.name}/")
            print("-" * 80)
            for csv_file in sorted(csv_files):
                if dry_run:
                    print(f"  Would delete: {csv_file.name}")
                else:
                    csv_file.unlink()
                    print(f"✗ Deleted: {csv_file.name}")
            print("-" * 80)
            print(f"Summary: {len(csv_files)} CSV files {'would be' if dry_run else 'were'} deleted")


def main():
    parser = argparse.ArgumentParser(
        description="Normalize SQL queries in YAML files to be Postgres-friendly"
    )
    parser.add_argument(
        "folder",
        type=str,
        nargs='?',
        default=None,
        help="Folder containing YAML files (relative to benchmarks/spider/)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all folders under benchmarks/spider/"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually modifying files"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="benchmarks/spider",
        help="Base directory for spider benchmarks (default: benchmarks/spider)"
    )

    args = parser.parse_args()

    if not args.all and not args.folder:
        parser.error("either provide a folder name or use --all")

    # Get the script directory and construct the path
    script_dir = Path(__file__).parent
    base_path = script_dir.parent / args.base_dir

    if args.all:
        folders = sorted([f for f in base_path.iterdir() if f.is_dir() and "[IGNORE]" not in f.name])
        for folder_path in folders:
            print(f"\n{'='*80}")
            print(f"  {folder_path.name}")
            print(f"{'='*80}")
            process_folder(folder_path, args.dry_run)
    else:
        folder_path = base_path / args.folder
        if not folder_path.exists():
            print(f"Error: Folder does not exist: {folder_path}")
            return 1
        process_folder(folder_path, args.dry_run)

    return 0


if __name__ == "__main__":
    exit(main())
