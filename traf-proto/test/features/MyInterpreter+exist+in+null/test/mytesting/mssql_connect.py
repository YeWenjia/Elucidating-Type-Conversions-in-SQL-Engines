import pyodbc

# Define connection parameters
server = 'localhost'  # e.g., 'localhost' or '127.0.0.1'
database = 'mssqldb'  # e.g., 'master'
username = 'sa'
password = 'reallyStrongPwd123'

# Connection string
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'


try:
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM TA")
        rows = cursor.fetchall()
        for row in rows:
          print(row)
        print("Connection successful!")
except Exception as e:
    print("Error connecting to SQL Server:", e)