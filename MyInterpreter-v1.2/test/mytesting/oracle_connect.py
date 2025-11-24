import oracledb

# Set up DSN (replace with actual host, port, and service_name)
dsn = oracledb.makedsn("localhost", "1521", service_name="FREE")

# Connect to Oracle Database
connection = oracledb.connect(
    user="myuser",
    password="password",
    dsn=dsn
)

# Test the connection
print("Successfully connected to Oracle Database version:", connection.version)

# Close the connection
connection.close()

# import cx_Oracle
#
# dsn = cx_Oracle.makedsn("localhost", 1521, service_name="FREE")
# connection = cx_Oracle.connect(user="myuser", password="password", dsn=dsn)
# cursor = connection.cursor()
#
# # 尝试不同的表名写法
# try:
#     cursor.execute('SELECT * FROM TA')  # 大写
#     print("✓ TA 成功")
# except:
#     try:
#         cursor.execute('SELECT * FROM ta')  # 小写
#         print("✓ ta 成功")
#     except:
#         try:
#             cursor.execute('SELECT * FROM "TA"')  # 带双引号大写
#             print("✓ \"TA\" 成功")
#         except:
#             try:
#                 cursor.execute('SELECT * FROM "ta"')  # 带双引号小写
#                 print("✓ \"ta\" 成功")
#             except Exception as e:
#                 print(f"✗ 都失败了: {e}")
#
# cursor.close()
# connection.close()
