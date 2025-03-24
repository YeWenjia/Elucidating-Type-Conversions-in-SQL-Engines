import pyodbc

# Define connection parameters
server = '127.0.0.1'  # e.g., 'localhost' or '127.0.0.1'
database = 'mssqldb'  # e.g., 'master'
username = 'sa'
password = 'reallyStrongPwd123'

# Connection string
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

try:
    with pyodbc.connect(conn_str) as conn:
        print("Connection successful!")
except Exception as e:
    print("Error connecting to SQL Server:", e)