"""
Spider Dataset Test Suite

Automatically validates each Spider subfolder by running YAML-defined SQL
against the matching database (PostgreSQL or MySQL) and comparing results between
the interpreter and the database engine.
"""

import re
import yaml
import psycopg2
import mysql.connector
import sqlite3
import pytest
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import oracledb
except ImportError:
    oracledb = None

from interpreter.lark_parser import LarkParser
from interpreter.syntax.engine.Postgres import Postgres
from interpreter.syntax.engine.Mysql import Mysql
from interpreter.syntax.engine.Sqlite import Sqlite
from interpreter.syntax.engine.Mssql import Mssql
from interpreter.syntax.engine.Oracle import Oracle
from interpreter.syntax.engine.Engine import Engine
from interpreter.Runtime import Eta
from interpreter.syntax.expression.BValue import *
from interpreter.Parser import Table
from interpreter.syntax.type.RelationType import RelationType, NameType
from interpreter.syntax.type.ValueType import SType, ZType, RType, DTType


# Base directory for spider benchmarks
SPIDER_BASE = Path(__file__).parent.parent.parent / "benchmarks" / "spider"
CONFIG_PATH = Path(__file__).parent.parent / "config.yml"

# Cache for loaded table data to avoid reloading on every test
# First test per schema loads data (~2 min for baseball_1), subsequent tests use cache (instant)
_TABLE_DATA_CACHE = {}

# Directory for SQLite database files (one per spider folder)
_SQLITE_DB_DIR = Path(__file__).parent.parent.parent / ".sqlite_cache"

# Engines to test (can be overridden via pytest command line: -k postgres, -k mysql, -k sqlite, -k mssql, -k oracle)
ENABLED_ENGINES = ['postgres', 'mysql', 'sqlite', 'mssql', 'oracle']

# Oracle tables use a prefix since Oracle schemas == users (creating users needs DBA privileges).
# All folders' tables live in the connecting user's schema with names like "activity_1__faculty".
ORACLE_TABLE_SEP = '__'
ORACLE_RESERVED_IDENTIFIERS = {'date', 'delegate', 'start', 'level', 'uid', 'year'}




def discover_spider_tests() -> List[Tuple[str, str, Path]]:
    """
    Discover all YAML test files in the spider benchmarks directory.
    
    Returns:
        List of (engine_name, folder_name, yaml_path) tuples for all enabled engines
    """
    test_cases = []
    
    if not SPIDER_BASE.exists():
        return test_cases
    
    # Find all directories under benchmarks/spider/
    for folder in sorted(SPIDER_BASE.iterdir()):
        if not folder.is_dir():
            continue
        
        folder_name = folder.name

        # Skip folders marked with [IGNORE]
        if "[IGNORE]" in folder_name:
            continue

        # Find all YAML files in this folder
        yaml_files = sorted(folder.glob("*.yaml"))
        for yaml_file in yaml_files:
            # Skip YAML files marked with [IGNORE]
            if "[IGNORE]" in yaml_file.name:
                continue
            # Generate test case for each enabled engine
            for engine_name in ENABLED_ENGINES:
                test_cases.append((engine_name, folder_name, yaml_file))
    
    return test_cases


def load_config():
    """Load database configuration from config.yml"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    
    # Fallback to default config
    return {
        'postgres': {
            'host': 'localhost',
            'port': 5432,
            'database': 'interpreter',
            'username': 'matiastoro',
            'password': ''
        },
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'database': 'interpreter',
            'username': 'root',
            'password': ''
        },
        'mssql': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'server': 'localhost,1433',
            'database': 'traf_spider',
            'username': 'sa',
            'password': ''
        },
        'oracle': {
            'user': 'myuser',
            'password': 'password',
            'dsn': 'localhost:1521/FREEPDB1'
        }
    }


def get_db_connection(engine_name: str, folder_name: str = None):
    """
    Create a database connection based on the engine type.
    
    Args:
        engine_name: Database engine ('postgres' or 'mysql')
        folder_name: Spider subfolder name (not used anymore, kept for compatibility)
        
    Returns:
        Database connection object (psycopg2 or mysql.connector connection)
    """
    config = load_config()
    
    if engine_name == 'postgres':
        postgres_config = config['postgres']
        
        # Connect to single traf_spider database
        db_name = "traf_spider"
        
        conn_params = {
            'host': postgres_config.get('host', 'localhost'),
            'port': postgres_config.get('port', 5432),
            'dbname': db_name,
            'user': postgres_config.get('username', 'postgres'),
            'password': postgres_config.get('password', '')
        }
        
        return psycopg2.connect(**conn_params)
    
    elif engine_name == 'mysql':
        mysql_config = config['mysql']

        conn_params = {
            'host': mysql_config.get('host', 'localhost'),
            'port': mysql_config.get('port', 3306),
            'user': mysql_config.get('username', 'root'),
            'password': mysql_config.get('password', '')
        }

        return mysql.connector.connect(**conn_params)

    elif engine_name == 'sqlite':
        # SQLite: one file per spider folder
        _SQLITE_DB_DIR.mkdir(exist_ok=True)
        db_path = _SQLITE_DB_DIR / f"{folder_name}.db"
        return sqlite3.connect(str(db_path))

    elif engine_name == 'mssql':
        if pyodbc is None:
            pytest.skip("pyodbc not installed; skipping MSSQL test")
        mssql_config = config['mssql']
        conn_str = (
            f"DRIVER={{{mssql_config.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
            f"SERVER={mssql_config.get('server', 'localhost')};"
            f"DATABASE={mssql_config.get('database', 'traf_spider')};"
            f"UID={mssql_config.get('username', 'sa')};"
            f"PWD={mssql_config.get('password', '')}"
        )
        conn = pyodbc.connect(conn_str, autocommit=False)
        return conn

    elif engine_name == 'oracle':
        if oracledb is None:
            pytest.skip("oracledb not installed; skipping Oracle test")
        oracle_config = config['oracle']
        conn_params = {
            'user': oracle_config.get('user'),
            'password': oracle_config.get('password', ''),
            'dsn': oracle_config.get('dsn'),
        }
        return oracledb.connect(**conn_params)

    else:
        raise ValueError(f"Unsupported engine: {engine_name}")


def _split_sql_statements(sql_script: str) -> List[str]:
    """Split a SQL script into individual statements on ';', ignoring separators inside strings."""
    statements = []
    buf = []
    in_string = False
    i = 0
    while i < len(sql_script):
        ch = sql_script[i]
        if ch == "'":
            # Toggle string; handle escaped '' as a pair
            if in_string and i + 1 < len(sql_script) and sql_script[i + 1] == "'":
                buf.append("''")
                i += 2
                continue
            in_string = not in_string
            buf.append(ch)
        elif ch == ';' and not in_string:
            stmt = ''.join(buf).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = ''.join(buf).strip()
    if tail and not tail.startswith('--'):
        statements.append(tail)
    return statements


def _apply_common_date_fixes(sql_script: str) -> str:
    """Normalize common date literal formats to ISO YYYY-MM-DD."""
    def _fix_date_dmy(m):
        d, mo, y = m.group(1), m.group(2), m.group(3)
        return f"'{y}-{mo}-{d.zfill(2)}'"
    sql_script = re.sub(r"'(\d{1,2})-(\d{2})-(\d{4})'", _fix_date_dmy, sql_script)

    def _fix_date_ymd(m):
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return f"'{y}-{mo.zfill(2)}-{d.zfill(2)}'"
    sql_script = re.sub(r"'(\d{4})-(\d{1,2})-(\d{1,2})'", _fix_date_ymd, sql_script)

    def _fix_datetime_mdy(m):
        mo, d, y, time = m.group(1), m.group(2), m.group(3), m.group(4) or ''
        return f"'{y}-{mo}-{d}{time}'"
    sql_script = re.sub(r"'(\d{2})/(\d{2})/(\d{4})(\s+\d{2}:\d{2}(?::\d{2})?)?'", _fix_datetime_mdy, sql_script)
    return sql_script


def _transform_sql_for_mssql(sql_script: str, schema_name: str) -> str:
    """Rewrite a spider db.sql script for MSSQL execution with a schema prefix."""
    # Remove BEGIN/COMMIT transaction wrappers
    sql_script = re.sub(r'^\s*BEGIN\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)
    sql_script = re.sub(r'^\s*COMMIT\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)

    # Replace backtick quoting with double quotes; then convert to [] later as needed
    sql_script = sql_script.replace('`', '"')

    # Normalize non-standard types to MSSQL-compatible types
    sql_script = re.sub(r'\bVARCHAR2\b', 'VARCHAR', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bNUMBER\b', 'DECIMAL', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bBOOLEAN\b', 'BIT', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bBOOL\b', 'BIT', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDOUBLE PRECISION\b', 'FLOAT', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDOUBLE\b', 'FLOAT', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bREAL\b', 'FLOAT', sql_script, flags=re.IGNORECASE)
    # MSSQL TIMESTAMP is a rowversion — use DATETIME2 for actual timestamps
    sql_script = re.sub(r'\bTIMESTAMP\b', 'DATETIME2', sql_script, flags=re.IGNORECASE)
    # TEXT in column definitions
    sql_script = re.sub(r'\bTEXT\b', 'VARCHAR(MAX)', sql_script, flags=re.IGNORECASE)
    # AUTOINCREMENT / AUTO_INCREMENT
    sql_script = re.sub(r'\bAUTO_?INCREMENT\b', 'IDENTITY(1,1)', sql_script, flags=re.IGNORECASE)

    sql_script = _apply_common_date_fixes(sql_script)

    # 'T' / 'F' boolean literals → 1 / 0
    sql_script = re.sub(r"(,\s*|\(\s*)'T'(\s*[,)])", r'\g<1>1\g<2>', sql_script)
    sql_script = re.sub(r"(,\s*|\(\s*)'F'(\s*[,)])", r'\g<1>0\g<2>', sql_script)

    # Qualify CREATE TABLE / INSERT INTO / REFERENCES / ALTER TABLE with schema
    def _qualify(keyword_re, keyword_out, sql):
        sql = re.sub(
            keyword_re + r'\s+"([^"]+)"',
            lambda m: f'{keyword_out} [{schema_name}].[{m.group(1).lower()}]',
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            keyword_re + r'\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            lambda m: f'{keyword_out} [{schema_name}].[{m.group(1).lower()}]',
            sql, flags=re.IGNORECASE
        )
        return sql

    sql_script = _qualify(r'CREATE\s+TABLE', 'CREATE TABLE', sql_script)
    sql_script = _qualify(r'INSERT\s+INTO', 'INSERT INTO', sql_script)
    sql_script = _qualify(r'REFERENCES', 'REFERENCES', sql_script)
    sql_script = _qualify(r'ALTER\s+TABLE', 'ALTER TABLE', sql_script)

    # Quote column names in column definitions to sidestep reserved words
    sql_script = re.sub(
        r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s+(INTEGER|INT|VARCHAR|CHAR|NVARCHAR|NCHAR|TEXT|DATETIME2|DATETIME|DATE|TIME|BIT|REAL|FLOAT|DECIMAL|NUMERIC|BLOB|SMALLINT|BIGINT|TINYINT)\b',
        r'\1[\2] \3',
        sql_script,
        flags=re.IGNORECASE
    )

    return sql_script


def _transform_sql_for_oracle(sql_script: str, folder_name: str) -> str:
    """Rewrite a spider db.sql script for Oracle using table-name prefixing."""
    prefix = f"{folder_name}{ORACLE_TABLE_SEP}"

    # Remove BEGIN/COMMIT
    sql_script = re.sub(r'^\s*BEGIN\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)
    sql_script = re.sub(r'^\s*COMMIT\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)

    sql_script = sql_script.replace('`', '"')
    # Oracle quoted identifiers are case-sensitive. Strip identifier quotes so
    # column definitions and later references like PRIMARY KEY(region_id) use
    # the same unquoted identifier semantics.
    sql_script = re.sub(r'"([A-Za-z_][A-Za-z0-9_]*)"', lambda m: m.group(1).lower(), sql_script)
    # Some Spider schemas contain quoted identifiers that are not practical in
    # Oracle DDL (for example "%_change_2007"). Normalize them to safe names.
    sql_script = sql_script.replace('"%_change_2007"', 'pct_change_2007')
    # Re-quote a small set of Oracle reserved identifiers that appear as column
    # names in Spider schemas. Unquoted, Oracle rejects them in DDL.
    reserved_pattern = "|".join(sorted(re.escape(name) for name in ORACLE_RESERVED_IDENTIFIERS))
    sql_script = re.sub(
        rf'(?im)^(\s*)({reserved_pattern})(\s+)',
        lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}',
        sql_script
    )

    # Normalize types to Oracle equivalents
    sql_script = re.sub(r'\bVARCHAR\s*\(\s*MAX\s*\)', 'VARCHAR2(4000)', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bVARCHAR\b', 'VARCHAR2', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bVARCHAR2\s*\(\s*(\d+)\s*\)', lambda m: f'VARCHAR2({min(int(m.group(1)), 4000)})', sql_script, flags=re.IGNORECASE)
    # Bare VARCHAR2 -> VARCHAR2(4000)
    sql_script = re.sub(r'\bVARCHAR2\b(?!\s*\()', 'VARCHAR2(4000)', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(
        r'(?im)^(\s*(?:"[^"]+"|`[^`]+`|[A-Za-z_][A-Za-z0-9_]*)\s+)TEXT\b',
        r'\1VARCHAR2(4000)',
        sql_script,
    )
    sql_script = re.sub(r'\bINT\s*\(\s*\d+\s*\)', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bINTEGER\s*\(\s*\d+\s*\)', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bINTEGER\b', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bINT\b', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bBIGINT\b', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bSMALLINT\b', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bTINYINT\b', 'NUMBER(3)', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bBOOLEAN\b', 'NUMBER(1)', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bBOOL\b', 'NUMBER(1)', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDECIMAL\b', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bNUMERIC\b', 'NUMBER', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDOUBLE\s+PRECISION\s*\(\s*\d+\s*\)', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDOUBLE\s*\(\s*\d+\s*\)', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    # SQLite REAL/FLOAT are 64-bit IEEE 754. Map to BINARY_DOUBLE (64-bit) so values
    # round-trip exactly — BINARY_FLOAT (32-bit) would corrupt literals like 102.76
    # so the interpreter's Decimal(str(float)) no longer matches the parsed literal.
    sql_script = re.sub(r'\bREAL\s*\(\s*\d+\s*\)', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bFLOAT\s*\(\s*\d+\s*\)', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDOUBLE PRECISION\b', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDOUBLE\b', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bREAL\b', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bFLOAT\b', 'BINARY_DOUBLE', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bDATETIME\b', 'TIMESTAMP', sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r'\bAUTO_?INCREMENT\b', 'GENERATED BY DEFAULT AS IDENTITY', sql_script, flags=re.IGNORECASE)
    # Spider DDL often carries MySQL-style DEFAULT clauses that Oracle rejects
    # or doesn't need for these tests. The inserts are explicit, so drop them.
    sql_script = re.sub(
        r'\s+DEFAULT\s+(NULL|\'[^\']*\'|-?\d+(?:\.\d+)?)',
        '',
        sql_script,
        flags=re.IGNORECASE,
    )

    sql_script = _apply_common_date_fixes(sql_script)
    # Oracle rejects MySQL-style zero dates. Preserve loadability by mapping
    # them to a stable sentinel date instead of NULL, since some Spider schemas
    # use these values in NOT NULL / primary-key columns.
    sql_script = re.sub(r"'0000-00-00 00:00:00'", "TIMESTAMP '0001-01-01 00:00:00'", sql_script)
    sql_script = re.sub(r"'0000-00-00 00:00'", "TIMESTAMP '0001-01-01 00:00:00'", sql_script)
    sql_script = re.sub(r"'0000-00-00'", "DATE '0001-01-01'", sql_script)
    # Oracle is sensitive to session NLS settings when inserting bare date/time
    # strings. Normalize ISO literals to ANSI DATE/TIMESTAMP literals.
    sql_script = re.sub(
        r"(?<!TIMESTAMP )'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'",
        r"TIMESTAMP '\1:00'",
        sql_script
    )
    sql_script = re.sub(
        r"(?<!TIMESTAMP )'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'",
        r"TIMESTAMP '\1'",
        sql_script
    )
    sql_script = re.sub(
        r"(?<!DATE )'(\d{4}-\d{2}-\d{2})'",
        r"DATE '\1'",
        sql_script
    )

    for reserved_name in sorted(ORACLE_RESERVED_IDENTIFIERS):
        sql_script = re.sub(
            rf'(?i)\bPRIMARY\s+KEY\s*\(([^)]*?)\b{re.escape(reserved_name)}\b([^)]*)\)',
            lambda m: f'PRIMARY KEY ({m.group(1)}"{reserved_name}"{m.group(2)})',
            sql_script
        )

    # 'T' / 'F' booleans → 1 / 0
    sql_script = re.sub(r"(,\s*|\(\s*)'T'(\s*[,)])", r'\g<1>1\g<2>', sql_script)
    sql_script = re.sub(r"(,\s*|\(\s*)'F'(\s*[,)])", r'\g<1>0\g<2>', sql_script)
    # Oracle treats '' as NULL, which breaks Spider schemas that insert empty
    # strings into NOT NULL text columns. Preserve a non-NULL placeholder.
    sql_script = re.sub(r'([,(]\s*)\'\'(\s*[,)\n])', r"\1' '\2", sql_script)
    # Oracle rejects a UNIQUE constraint that duplicates the PRIMARY KEY.
    sql_script = re.sub(
        r',\s*unique\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*(?=\))',
        '',
        sql_script,
        flags=re.IGNORECASE
    )

    # Prefix CREATE TABLE / INSERT INTO / REFERENCES / ALTER TABLE with folder
    def _prefix(keyword_re, keyword_out, sql):
        sql = re.sub(
            keyword_re + r'\s+"([^"]+)"',
            lambda m: f'{keyword_out} {prefix}{m.group(1).lower()}',
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            keyword_re + r'\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            lambda m: f'{keyword_out} {prefix}{m.group(1).lower()}',
            sql, flags=re.IGNORECASE
        )
        return sql

    sql_script = _prefix(r'\bCREATE\s+TABLE\b', 'CREATE TABLE', sql_script)
    sql_script = _prefix(r'\bINSERT\s+INTO\b', 'INSERT INTO', sql_script)
    sql_script = _prefix(r'\bREFERENCES\b', 'REFERENCES', sql_script)
    sql_script = _prefix(r'\bALTER\s+TABLE\b', 'ALTER TABLE', sql_script)

    return sql_script


def _drop_oracle_prefixed_tables(conn, folder_name: str):
    cur = conn.cursor()
    prefix = f"{folder_name}{ORACLE_TABLE_SEP}".upper()
    cur.execute(
        """
        SELECT table_name FROM user_tables
        WHERE table_name LIKE :1
        ORDER BY table_name DESC
        """,
        (f"{prefix}%",)
    )
    table_names = [row[0] for row in cur.fetchall()]
    for table_name in table_names:
        cur.execute(f'DROP TABLE {table_name} CASCADE CONSTRAINTS')


def _expected_spider_table_count(folder_name: str) -> Optional[int]:
    db_sql_path = SPIDER_BASE / folder_name / "tables" / "db.sql"
    if not db_sql_path.exists():
        return None
    sql_script = db_sql_path.read_text()
    return len(re.findall(r'(?im)^\s*CREATE\s+TABLE\b', sql_script))


def ensure_schema_and_tables(conn, engine_name: str, folder_name: str, force_recreate: bool = False):
    """
    Ensure schema/database exists for the folder and tables are created/populated.
    If schema doesn't exist, create it and load tables from db.sql.
    
    Args:
        conn: Database connection (psycopg2 or mysql.connector)
        engine_name: Database engine ('postgres' or 'mysql')
        folder_name: Spider subfolder name (e.g., 'activity_1')
    """
    import re
    
    cur = conn.cursor()
    
    if engine_name == 'postgres':
        # PostgreSQL: Use schemas within traf_spider database
        # Check if schema exists
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s
        """, (folder_name,))
        
        schema_exists = cur.fetchone() is not None
        
        if not schema_exists:
            print(f"Creating schema '{folder_name}' and loading tables...")
            
            # Create schema
            cur.execute(f'CREATE SCHEMA "{folder_name}"')
            
            # Find and execute db.sql file
            db_sql_path = SPIDER_BASE / folder_name / "tables" / "db.sql"
            
            if db_sql_path.exists():
                with open(db_sql_path, 'r') as f:
                    sql_script = f.read()
                
                # Normalize non-standard types to SQL standard
                sql_script = re.sub(r'\bVARCHAR2\b', 'VARCHAR', sql_script, flags=re.IGNORECASE)
                sql_script = re.sub(r'\bNUMBER\b', 'NUMERIC', sql_script, flags=re.IGNORECASE)
                sql_script = re.sub(r'\bDATETIME\b', 'TIMESTAMP', sql_script, flags=re.IGNORECASE)
                sql_script = re.sub(r'\bBOOL\b', 'BOOLEAN', sql_script, flags=re.IGNORECASE)
                sql_script = re.sub(r'\bDOUBLE\b(?!\s+PRECISION)', 'DOUBLE PRECISION', sql_script, flags=re.IGNORECASE)
                # Convert D(D)-MM-YYYY dates to YYYY-MM-DD (ISO format)
                def _fix_date_dmy(m):
                    d, mo, y = m.group(1), m.group(2), m.group(3)
                    return f"'{y}-{mo}-{d.zfill(2)}'"
                sql_script = re.sub(r"'(\d{1,2})-(\d{2})-(\d{4})'", _fix_date_dmy, sql_script)
                # Convert MM/DD/YYYY HH:MM to YYYY-MM-DD HH:MM (ISO format)
                def _fix_datetime_mdy(m):
                    mo, d, y, time = m.group(1), m.group(2), m.group(3), m.group(4)
                    return f"'{y}-{mo}-{d}{time}'"
                sql_script = re.sub(r"'(\d{2})/(\d{2})/(\d{4})(\s+\d{2}:\d{2}(?::\d{2})?)?'", _fix_datetime_mdy, sql_script)
                # Replace backtick quoting with double quotes for Postgres
                sql_script = sql_script.replace('`', '"')

                # Quote column names in column definitions to handle reserved words (start, end, etc.)
                sql_script = re.sub(
                    r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s+(INTEGER|VARCHAR|CHAR|TEXT|TIMESTAMP|DATE|TIME|BOOLEAN|REAL|FLOAT|DOUBLE PRECISION|DECIMAL|NUMERIC|BLOB|SMALLINT|BIGINT)\b',
                    r'\1"\2" \3',
                    sql_script,
                    flags=re.IGNORECASE
                )

                # Modify CREATE TABLE statements to use schema-qualified names (lowercase)
                sql_script = re.sub(
                    r'CREATE TABLE\s+"([^"]+)"',
                    lambda m: f'CREATE TABLE "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )
                sql_script = re.sub(
                    r'CREATE TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                    lambda m: f'CREATE TABLE "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )

                # Modify INSERT INTO statements to use schema-qualified names (lowercase)
                sql_script = re.sub(
                    r'INSERT INTO\s+"([^"]+)"',
                    lambda m: f'INSERT INTO "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )
                sql_script = re.sub(
                    r'INSERT INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                    lambda m: f'INSERT INTO "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )

                # Modify REFERENCES clauses to use schema-qualified names (lowercase)
                sql_script = re.sub(
                    r'REFERENCES\s+"([^"]+)"',
                    lambda m: f'REFERENCES "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )
                sql_script = re.sub(
                    r'REFERENCES\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                    lambda m: f'REFERENCES "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )
                
                # Modify ALTER TABLE statements to use schema-qualified names (lowercase)
                sql_script = re.sub(
                    r'ALTER TABLE\s+"([^"]+)"',
                    lambda m: f'ALTER TABLE "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )
                sql_script = re.sub(
                    r'ALTER TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                    lambda m: f'ALTER TABLE "{folder_name}"."{m.group(1).lower()}"',
                    sql_script,
                    flags=re.IGNORECASE
                )
                
                # Execute the modified script
                try:
                    cur.execute(sql_script)
                    conn.commit()
                    print(f"✓ Schema '{folder_name}' created and tables loaded")
                except Exception as e:
                    conn.rollback()
                    print(f"Error loading db.sql for {folder_name}: {e}")
                    raise
            else:
                print(f"Warning: db.sql not found at {db_sql_path}")
                conn.commit()
        else:
            # Schema exists, check if it has tables
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (folder_name,))
            
            table_count = cur.fetchone()[0]
            print(f"✓ Schema '{folder_name}' already exists with {table_count} tables")
    
    elif engine_name == 'mysql':
        # MySQL: Use schemas within traf_spider database (like PostgreSQL)
        # Check if schema (database) exists
        cur.execute("""
            SELECT SCHEMA_NAME 
            FROM information_schema.SCHEMATA
            WHERE SCHEMA_NAME = %s
        """, (folder_name,))
        
        schema_exists = cur.fetchone() is not None
        
        if not schema_exists:
            print(f"Creating schema '{folder_name}' and loading tables...")
            
            # Create schema (database in MySQL)
            cur.execute(f'CREATE DATABASE `{folder_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci')
            cur.execute(f'USE `{folder_name}`')
            
            # Find and execute db.sql file
            db_sql_path = SPIDER_BASE / folder_name / "tables" / "db.sql"
            
            if db_sql_path.exists():
                with open(db_sql_path, 'r') as f:
                    sql_script = f.read()
                
                # MySQL uses schemas (databases) like PostgreSQL
                # But we need to handle some syntax differences
                
                # Normalize non-standard types to SQL standard
                sql_script = re.sub(r'\bVARCHAR2\b', 'VARCHAR', sql_script, flags=re.IGNORECASE)
                sql_script = re.sub(r'\bNUMBER\b', 'NUMERIC', sql_script, flags=re.IGNORECASE)

                # Remove BEGIN; and COMMIT; transactions (MySQL autocommit is fine for DDL)
                sql_script = re.sub(r'^\s*BEGIN\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)
                sql_script = re.sub(r'^\s*COMMIT\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)
                
                # Convert PostgreSQL double-quoted identifiers to MySQL backtick-quoted
                sql_script = sql_script.replace('"', '`')

                # Replace timestamp with datetime for MySQL
                sql_script = re.sub(r'\btimestamp\b', 'datetime', sql_script, flags=re.IGNORECASE)

                # Convert D(D)-MM-YYYY dates to YYYY-MM-DD (ISO format)
                def _fix_date_dmy(m):
                    d, mo, y = m.group(1), m.group(2), m.group(3)
                    return f"'{y}-{mo}-{d.zfill(2)}'"
                sql_script = re.sub(r"'(\d{1,2})-(\d{2})-(\d{4})'", _fix_date_dmy, sql_script)
                # Convert MM/DD/YYYY HH:MM to YYYY-MM-DD HH:MM (ISO format)
                def _fix_datetime_mdy(m):
                    mo, d, y, time = m.group(1), m.group(2), m.group(3), m.group(4)
                    return f"'{y}-{mo}-{d}{time}'"
                sql_script = re.sub(r"'(\d{2})/(\d{2})/(\d{4})(\s+\d{2}:\d{2}(?::\d{2})?)?'", _fix_datetime_mdy, sql_script)

                # Replace text with VARCHAR(255) for MySQL (TEXT can't be used in keys)
                sql_script = re.sub(r'\btext\b', 'VARCHAR(255)', sql_script, flags=re.IGNORECASE)
                
                # Quote table names and column names with backticks for MySQL reserved words
                # Match CREATE TABLE and wrap table name in backticks
                sql_script = re.sub(
                    r'CREATE TABLE ([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'CREATE TABLE `\1`',
                    sql_script,
                    flags=re.IGNORECASE
                )
                
                # Quote column names in column definitions (column_name TYPE)
                # Match lines like "   rank VARCHAR(255)," and wrap column name
                sql_script = re.sub(
                    r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s+(INTEGER|VARCHAR|CHAR|TEXT|DECIMAL|FLOAT|DOUBLE|REAL|DATETIME|DATE|TIME|BOOLEAN|BLOB)\b',
                    r'\1`\2` \3',
                    sql_script,
                    flags=re.IGNORECASE
                )
                
                # Quote table names in INSERT INTO
                sql_script = re.sub(
                    r'INSERT INTO ([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'INSERT INTO `\1`',
                    sql_script,
                    flags=re.IGNORECASE
                )
                
                # Quote table names in REFERENCES
                sql_script = re.sub(
                    r'REFERENCES ([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'REFERENCES `\1`',
                    sql_script,
                    flags=re.IGNORECASE
                )
                
                # Quote column names in PRIMARY KEY constraints
                sql_script = re.sub(
                    r'PRIMARY KEY\s*\(([a-zA-Z_][a-zA-Z0-9_]*)\)',
                    r'PRIMARY KEY (`\1`)',
                    sql_script,
                    flags=re.IGNORECASE
                )
                
                # Quote column names in FOREIGN KEY constraints
                sql_script = re.sub(
                    r'FOREIGN KEY\s*\(([a-zA-Z_][a-zA-Z0-9_]*)\)',
                    r'FOREIGN KEY (`\1`)',
                    sql_script,
                    flags=re.IGNORECASE
                )

                # Replace 'T'/'F' boolean literals with TRUE/FALSE for MySQL
                sql_script = re.sub(r",\s*'T'\s*\)", ', TRUE)', sql_script)
                sql_script = re.sub(r",\s*'F'\s*\)", ', FALSE)', sql_script)

                # Execute statements one by one (MySQL connector may not handle multi-statement well)
                try:
                    # Split by semicolon but be careful with strings
                    statements = []
                    current_statement = []
                    in_string = False
                    escape_next = False
                    
                    for line in sql_script.split('\n'):
                        if not line.strip():
                            continue
                        
                        current_statement.append(line)
                        
                        # Simple check if line ends with semicolon (not perfect but works for our SQL files)
                        if line.rstrip().endswith(';'):
                            statements.append('\n'.join(current_statement))
                            current_statement = []
                    
                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            cur.execute(statement)
                    
                    # Stay in the folder's database
                    conn.commit()
                    print(f"✓ Schema '{folder_name}' created and tables loaded")
                except Exception as e:
                    conn.rollback()
                    print(f"Error loading db.sql for {folder_name}: {e}")
                    raise
            else:
                print(f"Warning: db.sql not found at {db_sql_path}")
                conn.commit()
        else:
            # Schema exists, check tables
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s
            """, (folder_name,))

            table_count = cur.fetchone()[0]
            print(f"✓ Schema '{folder_name}' already exists with {table_count} tables")

    elif engine_name == 'mssql':
        # MSSQL: Use schemas within a single database (configured in config.yml)
        cur.execute("""
            SELECT name FROM sys.schemas WHERE name = ?
        """, (folder_name,))
        schema_exists = cur.fetchone() is not None

        if not schema_exists:
            print(f"Creating MSSQL schema '{folder_name}' and loading tables...")
            cur.execute(f'CREATE SCHEMA [{folder_name}]')
            conn.commit()

            db_sql_path = SPIDER_BASE / folder_name / "tables" / "db.sql"
            if db_sql_path.exists():
                with open(db_sql_path, 'r') as f:
                    sql_script = f.read()

                sql_script = _transform_sql_for_mssql(sql_script, folder_name)

                try:
                    for stmt in _split_sql_statements(sql_script):
                        cur.execute(stmt)
                    conn.commit()
                    print(f"✓ MSSQL schema '{folder_name}' created and tables loaded")
                except Exception as e:
                    conn.rollback()
                    print(f"Error loading db.sql for {folder_name} (mssql): {e}")
                    raise
            else:
                print(f"Warning: db.sql not found at {db_sql_path}")
                conn.commit()
        else:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = ?
            """, (folder_name,))
            table_count = cur.fetchone()[0]
            print(f"✓ MSSQL schema '{folder_name}' already exists with {table_count} tables")

    elif engine_name == 'oracle':
        # Oracle: tables live in the connecting user's schema with a folder prefix
        # (schemas in Oracle == users, which require DBA privileges to create)
        prefix = f"{folder_name}{ORACLE_TABLE_SEP}".upper()
        cur.execute("""
            SELECT COUNT(*) FROM user_tables WHERE table_name LIKE :1
        """, (f"{prefix}%",))
        table_count = cur.fetchone()[0]
        expected_table_count = _expected_spider_table_count(folder_name)

        if (
            table_count > 0 and
            expected_table_count is not None and
            table_count != expected_table_count
        ):
            print(
                f"[DEBUG] Rebuilding Oracle tables for '{folder_name}' because existing table count "
                f"{table_count} != expected {expected_table_count}"
            )
            force_recreate = True

        # BINARY_FLOAT (32-bit) corrupts values like 102.76 and overflows sums of
        # 10^9-magnitude balances. The DDL now maps SQLite FLOAT/REAL to
        # BINARY_DOUBLE, so any pre-existing BINARY_FLOAT column indicates a stale
        # table from the old mapping and must be rebuilt.
        if table_count > 0 and not force_recreate:
            cur.execute(
                """
                SELECT COUNT(*) FROM user_tab_columns
                WHERE table_name LIKE :1 AND data_type = 'BINARY_FLOAT'
                """,
                (f"{prefix}%",),
            )
            stale_binary_float = cur.fetchone()[0]
            if stale_binary_float:
                print(
                    f"[DEBUG] Rebuilding Oracle tables for '{folder_name}' because {stale_binary_float} "
                    f"stale BINARY_FLOAT columns exist (now mapped to BINARY_DOUBLE)"
                )
                force_recreate = True

        if table_count > 0 and force_recreate:
            print(f"Recreating Oracle tables for '{folder_name}' with prefix '{prefix}'...")
            _drop_oracle_prefixed_tables(conn, folder_name)
            conn.commit()
            table_count = 0

        if table_count == 0:
            print(f"Creating Oracle tables for '{folder_name}' with prefix '{prefix}'...")

            db_sql_path = SPIDER_BASE / folder_name / "tables" / "db.sql"
            if db_sql_path.exists():
                with open(db_sql_path, 'r') as f:
                    sql_script = f.read()

                sql_script = _transform_sql_for_oracle(sql_script, folder_name)

                try:
                    for stmt in _split_sql_statements(sql_script):
                        cur.execute(stmt)
                    conn.commit()
                    print(f"✓ Oracle tables for '{folder_name}' created and loaded")
                except Exception as e:
                    conn.rollback()
                    print(f"Error loading db.sql for {folder_name} (oracle): {e}")
                    raise
            else:
                print(f"Warning: db.sql not found at {db_sql_path}")
        else:
            print(f"✓ Oracle tables for '{folder_name}' already exist ({table_count} tables)")

    elif engine_name == 'sqlite':
        # SQLite: check if any tables exist in the database file
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cur.fetchone()[0]

        if table_count == 0:
            print(f"Creating SQLite database for '{folder_name}' and loading tables...")

            db_sql_path = SPIDER_BASE / folder_name / "tables" / "db.sql"

            if db_sql_path.exists():
                with open(db_sql_path, 'r') as f:
                    sql_script = f.read()

                # Remove BEGIN/COMMIT - we'll use our own transaction
                sql_script = re.sub(r'^\s*BEGIN\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)
                sql_script = re.sub(r'^\s*COMMIT\s*;', '', sql_script, flags=re.IGNORECASE | re.MULTILINE)

                try:
                    cur.executescript(sql_script)
                    conn.commit()
                    print(f"✓ SQLite database '{folder_name}' created and tables loaded")
                except Exception as e:
                    conn.rollback()
                    print(f"Error loading db.sql for {folder_name}: {e}")
                    raise
            else:
                print(f"Warning: db.sql not found at {db_sql_path}")
        else:
            print(f"✓ SQLite database '{folder_name}' already exists with {table_count} tables")


def get_table_schema(conn, engine_name: str, table_name: str, schema_name: str) -> RelationType:
    """
    Get the schema for a table from the database.
    
    Args:
        conn: Database connection
        engine_name: Database engine ('postgres' or 'mysql')
        table_name: Name of the table
        schema_name: Schema/database containing the table
        
    Returns:
        RelationType object with column names and types
    """
    cur = conn.cursor()
    
    if engine_name == 'postgres':
        # Query to get column information from specific schema
        query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """
        
        cur.execute(query, (table_name.lower(), schema_name))
    elif engine_name == 'mysql':
        # MySQL: query from specific schema
        query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """

        cur.execute(query, (table_name.lower(), schema_name))
    elif engine_name == 'sqlite':
        # SQLite: use PRAGMA table_info
        cur.execute(f'PRAGMA table_info("{table_name}")')
        pragma_rows = cur.fetchall()
        # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
        columns = [(row[1], row[2].lower()) for row in pragma_rows]

        name_types = []
        for col_name, data_type in columns:
            if data_type in ('int', 'integer', 'bigint', 'smallint'):
                vtype = ZType()
            elif data_type in ('real', 'float', 'double', 'numeric', 'decimal'):
                vtype = RType()
            elif data_type in ('datetime', 'timestamp', 'date', 'time'):
                vtype = DTType()
            else:  # text, varchar, char, blob, etc.
                vtype = SType()
            name_types.append(NameType(col_name, vtype))

        return RelationType(name_types)
    elif engine_name == 'mssql':
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = ? AND table_schema = ?
            ORDER BY ordinal_position
            """,
            (table_name.lower(), schema_name)
        )
    elif engine_name == 'oracle':
        # schema_name is the folder name; actual Oracle table is prefixed and uppercased
        oracle_table = f"{schema_name}{ORACLE_TABLE_SEP}{table_name}".upper()
        cur.execute(
            """
            SELECT column_name, data_type, data_scale
            FROM user_tab_columns
            WHERE table_name = :1
            ORDER BY column_id
            """,
            (oracle_table,)
        )
    else:
        raise ValueError(f"Unsupported engine: {engine_name}")

    columns = cur.fetchall()

    name_types = []
    for row in columns:
        col_name, data_type = row[0], row[1]
        data_scale = row[2] if engine_name == 'oracle' and len(row) > 2 else None
        dtype = (data_type or '').lower().strip()
        # Oracle returns column names in uppercase (since we created tables without
        # quoting). Normalize to lowercase so the interpreter's dbt keys match.
        # Other engines preserve the original case — needed for quoted columns
        # like "home Town".
        if engine_name == 'oracle':
            # Oracle stores unquoted identifiers uppercased, but quoted identifiers
            # (for example %_change_2007) must be referenced using the exact name
            # returned by the catalog.
            if re.fullmatch(r'[A-Z][A-Z0-9_]*', col_name or ''):
                norm_name = col_name.lower()
            else:
                norm_name = col_name
        else:
            norm_name = col_name
        # Map across engines to interpreter types
        if dtype in ('integer', 'bigint', 'smallint', 'int', 'int4', 'int8', 'tinyint', 'mediumint'):
            vtype = ZType()
        elif dtype in ('real', 'double', 'double precision', 'numeric', 'decimal', 'float', 'float4', 'float8', 'money', 'smallmoney', 'binary_float', 'binary_double'):
            vtype = RType()
        elif dtype in ('date', 'timestamp', 'time', 'interval', 'timestamp without time zone', 'timestamp with time zone', 'datetime', 'datetime2', 'smalldatetime', 'datetimeoffset') or dtype.startswith('timestamp'):
            vtype = DTType()
        elif dtype == 'number':
            # Oracle NUMBER is generic. When a positive scale is declared (e.g.
            # DECIMAL(19,4) -> NUMBER(19,4)), the column stores decimals, so use
            # RType — otherwise the typechecker would cast values to Natural and
            # round 523.78 -> 524 in SELECT projections and INTERSECTs.
            if data_scale is not None and data_scale > 0:
                vtype = RType()
            else:
                vtype = ZType()
        elif dtype == 'bit':
            vtype = ZType()
        else:  # text, varchar, char, etc.
            vtype = SType()

        name_types.append(NameType(norm_name, vtype))

    return RelationType(name_types)


def load_table_data(conn, engine_name: str, table_name: str, schema_name: str, schema: RelationType) -> Table:
    """
    Load all data from a table into the interpreter's Table format.
    
    Args:
        conn: Database connection
        engine_name: Database engine ('postgres' or 'mysql')
        table_name: Name of the table
        schema_name: Schema/database containing the table
        schema: RelationType defining the table schema
        
    Returns:
        Table object with BValue rows
    """
    cur = conn.cursor()
    
    # Get column names from schema
    col_names = [nt.name for nt in schema.nametypes]
    
    # Fetch all rows - engine-specific quoting and qualification
    if engine_name == 'postgres':
        quoted_cols = [f'"{col}"' for col in col_names]
        query = f'SELECT {", ".join(quoted_cols)} FROM "{schema_name}"."{table_name}"'
    elif engine_name == 'mysql':
        # MySQL: Use backticks for quoting, schema-qualified like PostgreSQL
        quoted_cols = [f'`{col}`' for col in col_names]
        query = f'SELECT {", ".join(quoted_cols)} FROM `{schema_name}`.`{table_name}`'
    elif engine_name == 'sqlite':
        # SQLite: double quotes, no schema qualification needed
        quoted_cols = [f'"{col}"' for col in col_names]
        query = f'SELECT {", ".join(quoted_cols)} FROM "{table_name}"'
    elif engine_name == 'mssql':
        quoted_cols = [f'[{col}]' for col in col_names]
        query = f'SELECT {", ".join(quoted_cols)} FROM [{schema_name}].[{table_name}]'
    elif engine_name == 'oracle':
        # schema_name is the folder; actual table name has prefix
        oracle_table = f"{schema_name}{ORACLE_TABLE_SEP}{table_name}"
        quoted_cols = []
        for col in col_names:
            if col in ORACLE_RESERVED_IDENTIFIERS:
                quoted_cols.append(f'"{col}"')
            elif re.fullmatch(r'[a-z][a-z0-9_]*', col):
                quoted_cols.append(f'"{col.upper()}"')
            else:
                quoted_cols.append(f'"{col}"')
        query = f'SELECT {", ".join(quoted_cols)} FROM {oracle_table}'
    else:
        raise ValueError(f"Unsupported engine: {engine_name}")

    cur.execute(query)
    rows = cur.fetchall()
    
    # Convert to BValue format
    bvalue_rows = []
    for row in rows:
        bvalue_row = []
        for value in row:
            bv = BValue(value, use_decimal=True)
            bv.unknown = False
            bvalue_row.append(bv)
        bvalue_rows.append(bvalue_row)
    
    return Table(col_names, bvalue_rows)


def get_all_tables(conn, engine_name: str, schema_name: str) -> Tuple[dict, dict]:
    """
    Get all tables from the specified schema/database and create db and dbt dictionaries.
    
    Uses a module-level cache to avoid reloading table data on every test.
    Assumes if schema exists in database, data is already populated.
    
    Args:
        conn: Database connection
        engine_name: Database engine ('postgres' or 'mysql')
        schema_name: Name of the schema/database to load tables from
        
    Returns:
        Tuple of (db, dbt) where:
        - db: dict of table_name -> Table objects
        - dbt: dict of table_name -> RelationType objects (lowercase keys)
    """
    # Check cache first (cache key includes engine)
    cache_key = f"{engine_name}_{schema_name}"
    if cache_key in _TABLE_DATA_CACHE:
        return _TABLE_DATA_CACHE[cache_key]
    
    print(f"  Loading {schema_name} from {engine_name.upper()} (may take 1-2 min for large schemas)...")
    cur = conn.cursor()
    
    if engine_name == 'postgres':
        # Get all table names in this schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema_name,))
    elif engine_name == 'mysql':
        # MySQL: Get all tables in this schema
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema_name,))
    elif engine_name == 'sqlite':
        # SQLite: query sqlite_master for tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    elif engine_name == 'mssql':
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = ? AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (schema_name,)
        )
    elif engine_name == 'oracle':
        prefix = f"{schema_name}{ORACLE_TABLE_SEP}".upper()
        cur.execute(
            """
            SELECT table_name FROM user_tables
            WHERE table_name LIKE :1
            ORDER BY table_name
            """,
            (f"{prefix}%",)
        )
    else:
        raise ValueError(f"Unsupported engine: {engine_name}")

    if engine_name == 'oracle':
        # Strip the folder prefix so the interpreter sees unprefixed names
        prefix = f"{schema_name}{ORACLE_TABLE_SEP}".upper()
        table_names = [row[0][len(prefix):].lower() for row in cur.fetchall()]
    else:
        table_names = [row[0] for row in cur.fetchall()]
    
    db = {}
    dbt = {}
    
    # Load schema and data for each table
    retried_oracle_rebuild = False
    while True:
        try:
            for table_name in table_names:
                schema = get_table_schema(conn, engine_name, table_name, schema_name)
                dbt[table_name.lower()] = schema
                
                table = load_table_data(conn, engine_name, table_name, schema_name, schema)
                db[table_name.lower()] = table
            break
        except Exception as e:
            if engine_name == 'oracle' and not retried_oracle_rebuild and 'ORA-00904' in str(e):
                print(f"[DEBUG] Rebuilding Oracle tables for '{schema_name}' due to stale identifier mismatch: {e}")
                ensure_schema_and_tables(conn, engine_name, schema_name, force_recreate=True)
                cur.execute(
                    """
                    SELECT table_name FROM user_tables
                    WHERE table_name LIKE :1
                    ORDER BY table_name
                    """,
                    (f"{prefix}%",)
                )
                table_names = [row[0][len(prefix):].lower() for row in cur.fetchall()]
                db = {}
                dbt = {}
                retried_oracle_rebuild = True
                continue
            raise

    print(f"  Loaded {len(table_names)} tables")
    
    # Cache the result
    _TABLE_DATA_CACHE[cache_key] = (db, dbt)
    
    return db, dbt


def _qualify_mssql_identifiers(sql: str, dbt: dict, schema_name: str) -> str:
    """
    Prefix unqualified table references with [schema].[table] and bracket-quote column
    names to sidestep MSSQL reserved words. String literals are left untouched.
    """
    table_names = set(dbt.keys())
    column_names = set()
    for rel_type in dbt.values():
        for nt in rel_type.nametypes:
            column_names.add(nt.name.lower())
    column_only = column_names - table_names
    overlapping_names = table_names & column_names

    parts = re.split(r"('(?:[^'\\]|\\.)*')", sql)

    for i in range(len(parts)):
        if i % 2 == 0:
            segment = parts[i]
            # Qualify comma-separated table references only inside FROM clauses.
            segment = re.sub(
                r'(?is)\bFROM\b\s+([^;]+?)(?=\bWHERE\b|\bGROUP\s+BY\b|\bHAVING\b|\bORDER\s+BY\b|\bUNION\b|\bINTERSECT\b|\bEXCEPT\b|$)',
                lambda m: 'FROM ' + _qualify_mssql_from_list(m.group(1), table_names, schema_name),
                segment,
            )
            for ident in sorted(table_names, key=len, reverse=True):
                segment = re.sub(
                    r'(?i)\b(FROM|JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN)\s+'
                    + re.escape(ident) + r'\b',
                    lambda m: f'{m.group(1)} [{schema_name}].[{ident}]',
                    segment,
                )
            for ident in sorted(overlapping_names, key=len, reverse=True):
                segment = re.sub(
                    r'(?<![.\[])\b' + re.escape(ident) + r'\b(?!\])',
                    f'[{ident}]',
                    segment,
                    flags=re.IGNORECASE
                )
            for ident in sorted(column_only, key=len, reverse=True):
                segment = re.sub(
                    r'\b' + re.escape(ident) + r'\b',
                    f'[{ident}]',
                    segment,
                    flags=re.IGNORECASE
                )
            parts[i] = segment

    return ''.join(parts)


def _qualify_mssql_from_list(from_body: str, table_names: set, schema_name: str) -> str:
    parts = from_body.split(',')
    qualified = []
    for part in parts:
        updated = part
        for ident in sorted(table_names, key=len, reverse=True):
            updated = re.sub(
                r'(?i)^\s*' + re.escape(ident) + r'\b',
                lambda m: f'[{schema_name}].[{ident}]',
                updated,
            )
        qualified.append(updated)
    return ','.join(qualified)


def _rewrite_mssql_limit(sql: str) -> str:
    """
    Rewrite LIMIT/OFFSET syntax to T-SQL syntax.

    Current support is intentionally narrow and targets the Spider queries we run:
    - SELECT ... LIMIT n          -> SELECT TOP n ...
    - SELECT ... LIMIT n OFFSET m -> ... OFFSET m ROWS FETCH NEXT n ROWS ONLY

    The rewrite is applied to the innermost SELECT that owns each LIMIT, including
    LIMIT clauses inside subqueries.
    """
    limit_pattern = re.compile(r'\bLIMIT\s+(\d+)(?:\s+OFFSET\s+(\d+))?(?=\s*(?:\)|;|$))', flags=re.IGNORECASE)

    def _find_select_start(prefix: str) -> int | None:
        depth = 0
        in_string = False
        i = len(prefix) - 1
        while i >= 0:
            ch = prefix[i]
            if ch == "'":
                if in_string and i > 0 and prefix[i - 1] == "'":
                    i -= 2
                    continue
                in_string = not in_string
                i -= 1
                continue
            if in_string:
                i -= 1
                continue
            if ch == ')':
                depth += 1
                i -= 1
                continue
            if ch == '(':
                depth -= 1
                i -= 1
                continue
            if depth == 0 and i >= 5 and prefix[i - 5:i + 1].upper() == 'SELECT':
                prev_ok = i - 6 < 0 or (not prefix[i - 6].isalnum() and prefix[i - 6] != '_')
                next_ok = i + 1 >= len(prefix) or prefix[i + 1].isspace()
                if prev_ok and next_ok:
                    return i - 5
            i -= 1
        return None

    rewritten = sql
    while True:
        matches = list(limit_pattern.finditer(rewritten))
        if not matches:
            return rewritten

        limit_match = matches[-1]
        limit_n = int(limit_match.group(1))
        offset_n = int(limit_match.group(2)) if limit_match.group(2) is not None else None
        limit_start = limit_match.start()
        limit_end = limit_match.end()
        prefix = rewritten[:limit_start]
        suffix = rewritten[limit_end:]

        if offset_n is not None:
            rewritten = f"{prefix.rstrip()} OFFSET {offset_n} ROWS FETCH NEXT {limit_n} ROWS ONLY{suffix}"
            continue

        select_idx = _find_select_start(prefix)
        if select_idx is None:
            return rewritten

        select_end = select_idx + len('SELECT')
        without_limit = f"{prefix.rstrip()}{suffix}"
        rewritten = f"{without_limit[:select_end]} TOP {limit_n}{without_limit[select_end:]}"


def _rewrite_mssql_group_order_by(sql: str) -> str:
    """
    SQL Server requires ORDER BY expressions in grouped queries to be grouped or aggregated.
    For Spider queries that order grouped rows by a non-grouped base column, wrap the
    ORDER BY expression in MAX(...), which preserves the intended ordering for single-row
    groups and makes the query valid T-SQL.
    """
    if not re.search(r'\bGROUP\s+BY\b', sql, flags=re.IGNORECASE):
        return sql
    if not re.search(r'\bORDER\s+BY\b', sql, flags=re.IGNORECASE):
        return sql

    order_match = re.search(r'\bORDER\s+BY\s+(.+?)(;?\s*)$', sql, flags=re.IGNORECASE | re.DOTALL)
    if not order_match:
        return sql

    order_expr = order_match.group(1).strip()
    # Keep this rewrite deliberately narrow: one ORDER BY expression, optional ASC/DESC,
    # and skip anything already aggregated or compound.
    if ',' in order_expr:
        return sql

    direction = ''
    expr = order_expr
    m = re.match(r'(.+?)\s+(ASC|DESC)\s*$', order_expr, flags=re.IGNORECASE | re.DOTALL)
    if m:
        expr = m.group(1).strip()
        direction = ' ' + m.group(2).upper()

    if re.match(r'(?i)(COUNT|SUM|AVG|MIN|MAX)\s*\(', expr):
        return sql

    group_match = re.search(r'\bGROUP\s+BY\s+(.+?)\s+\bORDER\s+BY\b', sql, flags=re.IGNORECASE | re.DOTALL)
    if not group_match:
        return sql
    group_exprs = {part.strip().lower() for part in group_match.group(1).split(',')}
    if expr.strip().lower() in group_exprs:
        return sql

    replacement = f"ORDER BY MAX({expr}){direction}{order_match.group(2)}"
    return sql[:order_match.start()] + replacement


def _rewrite_mssql_group_select(sql: str) -> str:
    """
    SQL Server also requires non-aggregated SELECT expressions in grouped queries to
    appear in GROUP BY. For simple Spider patterns where a grouped SELECT projects a
    single base column, wrap that projection in MAX(...) when it is not grouped.
    """
    pattern = re.compile(
        r'(\bSELECT\s+)(.+?)(\s+\bFROM\b.+?\bGROUP\s+BY\s+)(.+?)(\s+\bHAVING\b)',
        flags=re.IGNORECASE | re.DOTALL
    )

    def _replace(match):
        select_prefix, select_expr, middle, group_by_exprs, suffix = match.groups()
        expr = select_expr.strip()
        if re.match(r'(?i)^DISTINCT\b', expr):
            return match.group(0)
        if ',' in expr:
            return match.group(0)
        if re.match(r'(?i)(COUNT|SUM|AVG|MIN|MAX)\s*\(', expr):
            return match.group(0)
        group_expr_set = {part.strip().lower() for part in group_by_exprs.split(',')}
        if expr.lower() in group_expr_set:
            return match.group(0)
        return f"{select_prefix}MAX({expr}){middle}{group_by_exprs}{suffix}"

    return pattern.sub(_replace, sql)


def _rewrite_mssql_subquery_order_by(sql: str) -> str:
    """
    SQL Server rejects ORDER BY inside subqueries unless TOP/OFFSET/FOR XML is present.
    For Spider IN-subqueries, ORDER BY has no semantic effect, so strip it when it
    appears directly before a closing parenthesis.
    """
    chars = list(sql)
    n = len(chars)
    i = 0

    while i < n:
        if sql[i:i + 8].upper() == 'ORDER BY':
            # Keep ORDER BY if the owning SELECT already has TOP, which makes
            # the subquery valid in SQL Server and preserves intended semantics.
            depth_back = 0
            in_string_back = False
            select_start = None
            p = i - 1
            while p >= 0:
                ch = chars[p]
                if ch == "'":
                    if in_string_back and p > 0 and chars[p - 1] == "'":
                        p -= 2
                        continue
                    in_string_back = not in_string_back
                    p -= 1
                    continue
                if in_string_back:
                    p -= 1
                    continue
                if ch == ')':
                    depth_back += 1
                elif ch == '(':
                    if depth_back == 0:
                        break
                    depth_back -= 1
                elif depth_back == 0 and p >= 5 and sql[p - 5:p + 1].upper() == 'SELECT':
                    prev_ok = p - 6 < 0 or (not chars[p - 6].isalnum() and chars[p - 6] != '_')
                    next_ok = p + 1 >= n or chars[p + 1].isspace()
                    if prev_ok and next_ok:
                        select_start = p - 5
                        break
                p -= 1

            if select_start is not None:
                select_head = sql[select_start:i].upper()
                if re.search(r'\bSELECT\s+TOP\b', select_head, flags=re.IGNORECASE):
                    i += 1
                    continue

            j = i + 8
            while j < n and chars[j].isspace():
                j += 1

            # If this ORDER BY already includes a SQL Server-compatible limiter,
            # leave it intact.
            tail = sql[j:]
            if re.search(r'\b(TOP|OFFSET|FOR\s+XML)\b', tail, flags=re.IGNORECASE):
                i = j
                continue

            depth = 0
            in_string = False
            k = j
            while k < n:
                ch = chars[k]
                if ch == "'":
                    if in_string and k + 1 < n and chars[k + 1] == "'":
                        k += 2
                        continue
                    in_string = not in_string
                    k += 1
                    continue
                if in_string:
                    k += 1
                    continue
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    if depth == 0:
                        del chars[i:k]
                        sql = ''.join(chars)
                        n = len(chars)
                        i = max(i - 1, 0)
                        break
                    depth -= 1
                k += 1
            else:
                break
        i += 1

    return ''.join(chars)


def _rewrite_mssql_operators(sql: str) -> str:
    """Normalize operators to T-SQL-friendly forms."""
    return sql.replace('!=', '<>')


def _prefix_oracle_tables(sql: str, dbt: dict, folder_name: str) -> str:
    """
    Oracle tables live in one schema with folder-based prefixes. Rewrite unqualified
    table references in the query so they resolve to the prefixed physical tables.
    """
    table_names = set(dbt.keys())
    prefix = f"{folder_name}{ORACLE_TABLE_SEP}"

    parts = re.split(r"('(?:[^'\\]|\\.)*')", sql)

    for i in range(len(parts)):
        if i % 2 == 0:
            segment = parts[i]
            segment = re.sub(
                r'(?is)\bFROM\b\s+('
                r'[A-Za-z0-9_]+(?:\s+(?:AS\s+)?[A-Za-z0-9_]+)?'
                r'(?:\s*,\s*[A-Za-z0-9_]+(?:\s+(?:AS\s+)?[A-Za-z0-9_]+)?)*'
                r')(?=\s+\bWHERE\b|\s+\bGROUP\s+BY\b|\s+\bHAVING\b|\s+\bORDER\s+BY\b|\s+\bJOIN\b|\s+\bUNION\b|\s+\bINTERSECT\b|\s+\bEXCEPT\b|\)|;|$)',
                lambda m: 'FROM ' + _prefix_oracle_from_list(m.group(1), table_names, prefix),
                segment,
            )
            for ident in sorted(table_names, key=len, reverse=True):
                segment = re.sub(
                    r'(?i)\bJOIN\s+' + re.escape(ident) + r'\b\s+AS\s+([A-Za-z0-9_]+)\b',
                    lambda m: f'JOIN {prefix}{ident} {m.group(1)}',
                    segment,
                )
                segment = re.sub(
                    r'(?i)\bJOIN\s+' + re.escape(ident) + r'\b\s+([A-Za-z0-9_]+)\b(?=\s+\bON\b)',
                    lambda m: f'JOIN {prefix}{ident} {m.group(1)}',
                    segment,
                )
                segment = re.sub(
                    r'(?i)\bJOIN\s+' + re.escape(ident) + r'\b(?=\s+\bON\b)',
                    lambda m: f'JOIN {prefix}{ident} {ident}',
                    segment,
                )
            segment = re.sub(
                r'(?i)\b(FROM|JOIN)\s+([A-Za-z0-9_]+)\s+AS\s+([A-Za-z0-9_]+)\b',
                r'\1 \2 \3',
                segment,
            )
            parts[i] = segment

    return ''.join(parts)


def _prefix_oracle_from_list(from_body: str, table_names: set, prefix: str) -> str:
    parts = from_body.split(',')
    prefixed = []
    for part in parts:
        updated = part
        for ident in sorted(table_names, key=len, reverse=True):
            updated = re.sub(
                r'(?i)^\s*' + re.escape(ident) + r'\b\s+AS\s+([A-Za-z0-9_]+)\b',
                lambda m: f'{prefix}{ident} {m.group(1)}',
                updated,
            )
            updated = re.sub(
                r'(?i)^\s*' + re.escape(ident) + r'\b\s+([A-Za-z0-9_]+)\b$',
                lambda m: f'{prefix}{ident} {m.group(1)}',
                updated,
            )
            updated = re.sub(
                r'(?i)^\s*' + re.escape(ident) + r'\b$',
                lambda m: f'{prefix}{ident} {ident}',
                updated,
            )
        updated = re.sub(
            r'(?i)^(\s*[A-Za-z0-9_]+)\s+([A-Za-z0-9_]+)\s+AS\s+([A-Za-z0-9_]+)\b',
            r'\1 \3',
            updated,
        )
        updated = re.sub(
            r'(?i)^(\s*[A-Za-z0-9_]+)\s+AS\s+([A-Za-z0-9_]+)\b',
            r'\1 \2',
            updated,
        )
        prefixed.append(updated)
    return ','.join(prefixed)




def _rewrite_oracle_operators(sql: str) -> str:
    return sql.replace('!=', '<>')


def _rewrite_oracle_setops(sql: str) -> str:
    # Oracle uses MINUS instead of EXCEPT.
    return re.sub(r'\bEXCEPT\b', 'MINUS', sql, flags=re.IGNORECASE)


def _quote_oracle_reserved_identifiers(sql: str) -> str:
    parts = re.split(r"('(?:[^'\\]|\\.)*')", sql)
    reserved_pattern = "|".join(sorted(re.escape(name) for name in ORACLE_RESERVED_IDENTIFIERS))
    for i in range(len(parts)):
        if i % 2 == 0:
            segment = parts[i]
            segment = re.sub(rf'(?i)(\.[ \t]*)({reserved_pattern})\b', r'\1"\2"', segment)
            segment = re.sub(
                rf'(?i)(?<![\w".])({reserved_pattern})\b(?!\s*\')',
                r'"\1"',
                segment,
            )
            parts[i] = segment
    return ''.join(parts)


def _rewrite_oracle_limit(sql: str) -> str:
    limit_pattern = re.compile(r'\bLIMIT\s+(\d+)(?:\s+OFFSET\s+(\d+))?(?=\s*(?:\)|;|$))', flags=re.IGNORECASE)
    rewritten = sql
    while True:
        matches = list(limit_pattern.finditer(rewritten))
        if not matches:
            return rewritten
        m = matches[-1]
        limit_n = int(m.group(1))
        offset_n = int(m.group(2)) if m.group(2) is not None else None
        replacement = (
            f'OFFSET {offset_n} ROWS FETCH NEXT {limit_n} ROWS ONLY'
            if offset_n is not None else
            f'FETCH FIRST {limit_n} ROWS ONLY'
        )
        rewritten = rewritten[:m.start()] + replacement + rewritten[m.end():]


def _rewrite_oracle_group_order_by(sql: str) -> str:
    if not re.search(r'\bGROUP\s+BY\b', sql, flags=re.IGNORECASE):
        return sql
    if not re.search(r'\bORDER\s+BY\b', sql, flags=re.IGNORECASE):
        return sql

    order_match = re.search(r'\bORDER\s+BY\s+(.+?)(;?\s*)$', sql, flags=re.IGNORECASE | re.DOTALL)
    if not order_match:
        return sql

    order_expr = order_match.group(1).strip()
    if ',' in order_expr:
        return sql

    direction = ''
    expr = order_expr
    m = re.match(r'(.+?)\s+(ASC|DESC)\s*$', order_expr, flags=re.IGNORECASE | re.DOTALL)
    if m:
        expr = m.group(1).strip()
        direction = ' ' + m.group(2).upper()

    if re.match(r'(?i)(COUNT|SUM|AVG|MIN|MAX)\s*\(', expr):
        return sql

    group_match = re.search(r'\bGROUP\s+BY\s+(.+?)\s+\bORDER\s+BY\b', sql, flags=re.IGNORECASE | re.DOTALL)
    if not group_match:
        return sql
    group_exprs = {part.strip().lower() for part in group_match.group(1).split(',')}
    if expr.strip().lower() in group_exprs:
        return sql

    replacement = f"ORDER BY MAX({expr}){direction}{order_match.group(2)}"
    return sql[:order_match.start()] + replacement


def _rewrite_oracle_group_select(sql: str) -> str:
    pattern = re.compile(
        r'(\bSELECT\s+)(.+?)(\s+\bFROM\b.+?\bGROUP\s+BY\s+)(.+?)(?=\s+\bHAVING\b|\s+\bORDER\s+BY\b|;|$)',
        flags=re.IGNORECASE | re.DOTALL
    )

    def _replace(match):
        select_prefix, select_expr, middle, group_by_exprs = match.groups()
        # Skip if the GROUP BY belongs to a subquery (unbalanced parens in middle)
        if middle.count('(') != middle.count(')'):
            return match.group(0)
        expr = select_expr.strip()
        if re.match(r'(?i)^DISTINCT\b', expr):
            return match.group(0)
        group_expr_set = {part.strip().lower() for part in group_by_exprs.split(',')}
        select_parts = [part.strip() for part in select_expr.split(',')]
        rewritten_parts = []
        changed = False
        for part in select_parts:
            if re.match(r'(?i)(COUNT|SUM|AVG|MIN|MAX)\s*\(', part):
                rewritten_parts.append(part)
            elif part.lower() in group_expr_set:
                rewritten_parts.append(part)
            else:
                rewritten_parts.append(f"MAX({part})")
                changed = True
        if not changed:
            return match.group(0)
        return f"{select_prefix}{', '.join(rewritten_parts)}{middle}{group_by_exprs}"

    return pattern.sub(_replace, sql)


def _rewrite_oracle_subquery_order_by(sql: str) -> str:
    chars = list(sql)
    n = len(chars)
    i = 0
    while i < n:
        if sql[i:i + 8].upper() == 'ORDER BY':
            j = i + 8
            while j < n and chars[j].isspace():
                j += 1

            # Keep ORDER BY when the same subquery already includes a row-limiting
            # clause after the ORDER BY. Oracle requires ORDER BY for FETCH FIRST.
            depth_ahead = 0
            in_string_ahead = False
            k = j
            order_by_end = None
            while k < n:
                ch = chars[k]
                if ch == "'":
                    if in_string_ahead and k + 1 < n and chars[k + 1] == "'":
                        k += 2
                        continue
                    in_string_ahead = not in_string_ahead
                    k += 1
                    continue
                if in_string_ahead:
                    k += 1
                    continue
                if ch == '(':
                    depth_ahead += 1
                elif ch == ')':
                    if depth_ahead == 0:
                        order_by_end = k
                        break
                    depth_ahead -= 1
                elif ch == ';' and depth_ahead == 0:
                    order_by_end = k
                    break
                k += 1
            if order_by_end is None:
                order_by_end = n

            order_by_tail = sql[j:order_by_end].upper()
            if re.search(r'\b(FETCH\s+FIRST|OFFSET\s+\d+\s+ROWS)\b', order_by_tail, flags=re.IGNORECASE):
                i += 1
                continue

            depth = 0
            in_string = False
            k = j
            while k < n:
                ch = chars[k]
                if ch == "'":
                    if in_string and k + 1 < n and chars[k + 1] == "'":
                        k += 2
                        continue
                    in_string = not in_string
                    k += 1
                    continue
                if in_string:
                    k += 1
                    continue
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    if depth == 0:
                        del chars[i:k]
                        sql = ''.join(chars)
                        n = len(chars)
                        i = max(i - 1, 0)
                        break
                    depth -= 1
                k += 1
            else:
                break
        i += 1
    return ''.join(chars)


def _quote_oracle_numeric_literals_for_string_cols(sql: str, dbt: dict) -> str:
    """
    When a VARCHAR column is compared with a numeric literal, Oracle implicitly
    coerces the column's values to NUMBER, which fails with ORA-01722 on any row
    whose value isn't parseable (e.g. hours = '4-6:20' in college_3.course).

    Make the implicit conversion explicit with TO_NUMBER(...) so Oracle cannot
    hide conversion errors through predicate reordering/short-circuiting.
    Quoting the numeric literal would force lexicographic comparison, which
    disagrees with the interpreter for operators like <, <=, >, >=.
    """
    string_cols = set()
    numeric_cols = set()
    for rel in dbt.values():
        for nt in rel.nametypes:
            if isinstance(nt.type, SType):
                string_cols.add(nt.name.lower())
            elif isinstance(nt.type, (ZType, RType)):
                numeric_cols.add(nt.name.lower())

    cmp_pattern = None
    agg_pattern = None
    if string_cols:
        scol_pat = '|'.join(re.escape(c) for c in sorted(string_cols, key=len, reverse=True))
        cmp_pattern = re.compile(
            rf'(?i)(?<![\w.])((?:[A-Za-z_]\w*\.)?(?:{scol_pat}))\s*(=|<>|<=|>=|<|>)\s*(-?\d+(?:\.\d+)?)(?!\w|\.)'
        )
        # Aggregate functions over a VARCHAR column also trigger TO_NUMBER coercion
        # (e.g. SUM(order_quantity) blows up on 'm'). The interpreter's resolve_agg_func
        # casts SType -> RType for SUM/AVG, so wrap those too.
        agg_pattern = re.compile(
            rf'(?i)\b(SUM|AVG)\s*\(\s*((?:[A-Za-z_]\w*\.)?(?:{scol_pat}))\s*\)'
        )

    use_null_on_column_conversion_error = bool(re.search(r'(?i)\bJOIN\b', sql))

    def _to_number_column(col: str) -> str:
        if use_null_on_column_conversion_error:
            return f"TO_NUMBER({col} DEFAULT NULL ON CONVERSION ERROR)"
        return f"TO_NUMBER({col})"

    def _wrap_cmp(m):
        col, op, num = m.group(1), m.group(2), m.group(3)
        unqualified = col.split('.')[-1].lower()
        if unqualified in string_cols:
            return f"{_to_number_column(col)} {op} {num}"
        return m.group(0)

    def _wrap_agg(m):
        fn, col = m.group(1), m.group(2)
        unqualified = col.split('.')[-1].lower()
        if unqualified in string_cols:
            return f"{fn}(TO_NUMBER({col}))"
        return m.group(0)

    # Numeric column compared with a string literal (e.g. manager_id != 'null'):
    # Oracle tries TO_NUMBER on the literal and may blow up on 'null'. Make the
    # conversion explicit so optimizer predicate ordering does not mask the error.
    num_col_cmp_end = None
    if numeric_cols:
        ncol_pat = '|'.join(re.escape(c) for c in sorted(numeric_cols, key=len, reverse=True))
        num_col_cmp_end = re.compile(
            rf'(?i)((?:[A-Za-z_]\w*\.)?(?:{ncol_pat}))\s*(=|<>|<=|>=|<|>)\s*$'
        )

    parts = re.split(r"('(?:[^'\\]|\\.)*')", sql)
    for i in range(len(parts)):
        if i % 2 == 0:
            segment = parts[i]
            if cmp_pattern is not None:
                segment = cmp_pattern.sub(_wrap_cmp, segment)
            if agg_pattern is not None:
                segment = agg_pattern.sub(_wrap_agg, segment)
            parts[i] = segment

    if num_col_cmp_end is not None:
        for i in range(1, len(parts), 2):
            literal = parts[i]
            prev = parts[i - 1]
            m = num_col_cmp_end.search(prev)
            if not m:
                continue
            col, op = m.group(1), m.group(2)
            unqualified = col.split('.')[-1].lower()
            # Some Spider schemas reuse the same column name across string and numeric
            # columns in different tables (e.g. campuses.campus TEXT vs degrees.campus INT).
            # In that case we can't safely infer the type from the bare column name here.
            if unqualified in string_cols:
                continue
            parts[i - 1] = prev[:m.start()]
            parts[i] = f"{col} {op} TO_NUMBER({literal})"

    return ''.join(parts)


def _probe_oracle_to_number_conversions(cur, sql: str, dbt: dict):
    """Force Oracle to validate explicit TO_NUMBER casts that the optimizer may skip."""
    for m in re.finditer(r"(?is)\bTO_NUMBER\s*\(\s*('(?:[^']|'')*')\s*\)", sql):
        cur.execute(f"SELECT TO_NUMBER({m.group(1)}) FROM dual")
        cur.fetchall()

    from_match = re.search(
        r'(?is)\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+([A-Za-z_][A-Za-z0-9_]*))?',
        sql,
    )
    if not from_match:
        return

    table_name = from_match.group(1)
    table_by_alias = {}

    for table_match in re.finditer(
        r'(?is)\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+([A-Za-z_][A-Za-z0-9_]*))?',
        sql,
    ):
        physical_table = table_match.group(1)
        alias = table_match.group(2)
        if alias and alias.upper() in {'ON', 'WHERE', 'GROUP', 'HAVING', 'ORDER', 'UNION', 'INTERSECT', 'MINUS', 'FETCH', 'OFFSET'}:
            alias = None
        table_by_alias[physical_table.lower()] = physical_table
        if alias:
            table_by_alias[alias.lower()] = physical_table

    def _logical_table_name(physical_name: str) -> str:
        name = physical_name.lower()
        if ORACLE_TABLE_SEP in name:
            return name.split(ORACLE_TABLE_SEP, 1)[1]
        return name

    def _table_has_column(physical_name: str, column_name: str) -> bool:
        rel = dbt.get(_logical_table_name(physical_name))
        if rel is None:
            return False
        return any(nt.name.lower() == column_name.lower() for nt in rel.nametypes)

    source_match = re.search(
        r'(?is)\bFROM\b\s+(.+?)(?=\s+\bWHERE\b|\s+\bGROUP\s+BY\b|\s+\bHAVING\b|\s+\bORDER\s+BY\b|\s+\bUNION\b|\s+\bINTERSECT\b|\s+\bMINUS\b|\s+\bFETCH\b|\s+\bOFFSET\b|$)',
        sql,
    )
    source_clause = f"FROM {source_match.group(1).strip()}" if source_match else None

    for m in re.finditer(r"(?is)\bTO_NUMBER\s*\(\s*([^()']+?)\s*\)", sql):
        expr = m.group(1).strip()
        if re.search(r'(?i)\bDEFAULT\b', expr):
            prefix = sql[max(0, m.start() - 12):m.start()]
            if source_clause and not re.search(r'(?i)AVG\s*\(\s*$', prefix):
                strict_expr = re.sub(r'(?i)\s+DEFAULT\s+NULL\s+ON\s+CONVERSION\s+ERROR\s*$', '', expr).strip()
                if re.match(r'^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$', strict_expr):
                    cur.execute(f"SELECT TO_NUMBER({strict_expr}) {source_clause}")
                    cur.fetchall()
            continue
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$', expr):
            continue
        if '.' in expr:
            qualifier, col = expr.split('.', 1)
            source_table = table_by_alias.get(qualifier.lower())
            if source_table is None:
                continue
        else:
            col = expr
            candidate_tables = [
                physical_name
                for physical_name in dict.fromkeys(table_by_alias.values())
                if _table_has_column(physical_name, col)
            ]
            source_table = candidate_tables[0] if len(candidate_tables) == 1 else table_name
        cur.execute(f"SELECT TO_NUMBER({col}) FROM {source_table}")
        cur.fetchall()


def _quote_mysql_identifiers(sql: str, dbt: dict) -> str:
    """
    Quote table and column names with backticks for MySQL, skipping string literals.
    Splits the SQL into string-literal vs non-literal segments, only replacing in non-literals.
    """
    import re as _re

    # Collect all identifiers (table names + column names)
    all_identifiers = set(dbt.keys())
    for rel_type in dbt.values():
        for nt in rel_type.nametypes:
            all_identifiers.add(nt.name.lower())

    # Split SQL into segments: alternating non-string / string-literal parts
    # Matches single-quoted strings (with escaped quotes handled)
    parts = _re.split(r"('(?:[^'\\]|\\.)*')", sql)

    for i in range(len(parts)):
        # Even indices are outside strings, odd indices are string literals
        if i % 2 == 0:
            segment = parts[i]
            for ident in sorted(all_identifiers, key=len, reverse=True):
                segment = _re.sub(
                    r'\b' + _re.escape(ident) + r'\b',
                    f'`{ident}`',
                    segment,
                    flags=_re.IGNORECASE
                )
            parts[i] = segment

    return ''.join(parts)


# Generate test parameters
test_params = discover_spider_tests()


@pytest.mark.parametrize("engine_name,folder_name,yaml_path", test_params, 
                         ids=[f"{engine}_{folder}/{yaml.stem}" for engine, folder, yaml in test_params])
def test_spider_query(engine_name: str, folder_name: str, yaml_path: Path):
    """
    Test a single Spider query by comparing interpreter results with database engine.
    
    Args:
        engine_name: Database engine to test against ('postgres' or 'mysql')
        folder_name: Spider subfolder name
        yaml_path: Path to YAML file containing the query
    """
    # Load YAML file
    with open(yaml_path, "r") as f:
        yaml_data = yaml.safe_load(f)
    
    sql_query = yaml_data.get('sql', '').strip()
    if not sql_query:
        pytest.skip("No SQL query in YAML file")
    
    # Make sure query ends with semicolon
    if not sql_query.endswith(';'):
        sql_query += ';'
    
    print(f"\n{'='*80}")
    print(f"Testing: {engine_name.upper()} - {folder_name}/{yaml_path.stem}")
    print(f"SQL: {sql_query}")
    print(f"{'='*80}\n")
    
    # Connect to the appropriate database
    conn = None
    try:
        print(f"[DEBUG] Getting {engine_name} connection for {folder_name}")
        conn = get_db_connection(engine_name, folder_name)
        print(f"[DEBUG] Connection established")
        
        # Ensure schema and tables exist for this folder
        print(f"[DEBUG] Ensuring schema and tables exist...")
        ensure_schema_and_tables(conn, engine_name, folder_name)
        print(f"[DEBUG] Schema and tables ready")
        
        # Load all tables from the schema
        print(f"[DEBUG] Loading all tables from schema...")
        db, dbt = get_all_tables(conn, engine_name, folder_name)
        print(f"[DEBUG] Tables loaded, starting test execution")
        
        # Initialize parser and engine
        parser = LarkParser(schema=dbt)
        if engine_name == 'postgres':
            engine = Postgres()
        elif engine_name == 'mysql':
            engine = Mysql()
        elif engine_name == 'mssql':
            engine = Mssql()
        elif engine_name == 'oracle':
            engine = Oracle()
        else:
            engine = Sqlite()
        
        # Parse the SQL query
        try:
            parsed = parser.parse(sql_query)
            print(f"Parsed query: {parsed}")
            print(f"Parsed query: {parsed.__repr__()}")
        except Exception as e:
            pytest.fail(f"Failed to parse SQL: {e}")
        
        # Run in interpreter
        our_result = None
        our_error = None
        try:
            TQ = engine.typechecker.typecheck_query(dbt, RelationType([]), parsed)
            T = TQ[0]
            qp = TQ[1]
            print(f"Type: {T}")
            print(f"Translated query: {qp}")
            
            our_result = engine.run.run_query(db, Eta([], []), qp)
            print(f"Interpreter result: {our_result.rows}")
        except Exception as e:
            our_error = e
            print(f"Interpreter error: {e}")
            # Don't raise - continue to test database
        
        # Run in database engine
        their_result = None
        their_error = None

        def _build_oracle_query(query, dbt_):
            q = re.sub(r'\b(COUNT|SUM|AVG|MAX|MIN)\s+\(', r'\1(', query, flags=re.IGNORECASE)
            q = _prefix_oracle_tables(q, dbt_, folder_name)
            q = _rewrite_oracle_operators(q)
            q = _rewrite_oracle_setops(q)
            q = _quote_oracle_reserved_identifiers(q)
            q = _quote_oracle_numeric_literals_for_string_cols(q, dbt_)
            q = _rewrite_oracle_limit(q)
            q = _rewrite_oracle_group_select(q)
            q = _rewrite_oracle_group_order_by(q)
            q = _rewrite_oracle_subquery_order_by(q)
            return q.rstrip().rstrip(';')

        try:
            cur = conn.cursor()

            # Set schema context for unqualified table name resolution
            if engine_name == 'postgres':
                # PostgreSQL: use SET search_path
                cur.execute(f'SET search_path TO "{folder_name}", public')
            elif engine_name == 'mysql':
                # MySQL: set default database
                cur.execute(f'USE `{folder_name}`')
            # SQLite: no schema context needed (each DB file is its own namespace)
            # MSSQL: we schema-qualify table refs in the rewritten query
            # Oracle: we prefix table refs in the rewritten query

            # Normalize SQL for target engine
            db_sql_query = sql_query
            # Remove spaces between function names and '(' (MySQL doesn't allow it)
            db_sql_query = re.sub(r'\b(COUNT|SUM|AVG|MAX|MIN)\s+\(', r'\1(', db_sql_query, flags=re.IGNORECASE)
            if engine_name == 'mysql':
                db_sql_query = _quote_mysql_identifiers(db_sql_query, dbt)
            elif engine_name == 'mssql':
                db_sql_query = _qualify_mssql_identifiers(db_sql_query, dbt, folder_name)
                db_sql_query = _rewrite_mssql_operators(db_sql_query)
                db_sql_query = _rewrite_mssql_limit(db_sql_query)
                db_sql_query = _rewrite_mssql_group_select(db_sql_query)
                db_sql_query = _rewrite_mssql_group_order_by(db_sql_query)
                db_sql_query = _rewrite_mssql_subquery_order_by(db_sql_query)
            elif engine_name == 'oracle':
                db_sql_query = _build_oracle_query(sql_query, dbt)
                _probe_oracle_to_number_conversions(cur, db_sql_query, dbt)

            print(f"[DEBUG] Executing query on {engine_name}: {db_sql_query}")
            try:
                cur.execute(db_sql_query)
            except Exception as exec_err:
                if engine_name == 'oracle' and 'ORA-00904' in str(exec_err):
                    print(f"[DEBUG] ORA-00904 on query — rebuilding Oracle tables for '{folder_name}' and retrying: {exec_err}")
                    conn.rollback()
                    _TABLE_DATA_CACHE.pop(f"{engine_name}_{folder_name}", None)
                    ensure_schema_and_tables(conn, engine_name, folder_name, force_recreate=True)
                    conn.commit()
                    db, dbt = get_all_tables(conn, engine_name, folder_name)
                    cur = conn.cursor()
                    db_sql_query = _build_oracle_query(sql_query, dbt)
                    _probe_oracle_to_number_conversions(cur, db_sql_query, dbt)
                    print(f"[DEBUG] Re-executing query on {engine_name}: {db_sql_query}")
                    cur.execute(db_sql_query)
                else:
                    raise

            column_names = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            their_result = rows
            print(f"{engine_name.upper()} result: {rows}")
            print(f"Columns: {column_names}")
        except Exception as e:
            their_error = e
            print(f"{engine_name.upper()} error: {e}")
        finally:
            conn.rollback()
        
        # Compare results
        if our_error and their_error:
            # Both failed - this is considered a pass (they agree there's an error)
            print(f"✓ Both interpreter and {engine_name.upper()} failed (agreement on error)")
            assert True
        elif our_error and not their_error:
            pytest.fail(f"Interpreter failed but {engine_name.upper()} succeeded.\nInterpreter error: {our_error}\n{engine_name.upper()} result: {their_result}")
        elif not our_error and their_error:
            pytest.fail(f"{engine_name.upper()} failed but interpreter succeeded.\n{engine_name.upper()} error: {their_error}\nInterpreter result: {our_result.rows}")
        else:
            # Both succeeded - compare results
            compare_result = Engine().Compare(our_result.rows, their_result, engine)
            if not compare_result:
                print(f"\nMISMATCH:")
                print(f"  Interpreter: {our_result.rows}")
                print(f"  {engine_name.upper()}:  {their_result}")
                pytest.fail(f"Results do not match between interpreter and {engine_name.upper()}")
            else:
                print("✓ Results match!")
    
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__, "-v"])
