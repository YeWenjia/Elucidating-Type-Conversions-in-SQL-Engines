import cx_Oracle

# Set up DSN (replace with actual host, port, and service_name)
dsn = cx_Oracle.makedsn("localhost", "1521", service_name="XE")

# Connect to Oracle Database
connection = cx_Oracle.connect(
    user="myuser",
    password="password",
    dsn=dsn
)

# Test the connection
print("Successfully connected to Oracle Database version:", connection.version)

# Close the connection
connection.close()