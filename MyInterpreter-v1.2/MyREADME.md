# eSeQueeLe

#### Postgresql

psql postgres


1. You should log in to the PostgreSQL server, you can create a new database by running the following command:

`CREATE DATABASE interpreter;`

2. You can create a new user by running the following command:

`CREATE USER myuser WITH PASSWORD 'myuser';`


3. ou can grant the new user permission to access the new database by running the following command:

`GRANT ALL PRIVILEGES ON DATABASE interpreter TO myuser;`


4. You could log in to the database using the 'myuser' by running 
the following command:

`psql -d interpreter -U myuser`

and you are required to fill in the password:

`myuser`


#### Sqlite

1. create the database by the following command:

`sqlite3 mydatabase.db`

2. fill in the path to mydatabase.db to the file config

3. log in to the database everytime using the command:

`sqlite3 mydatabase.db`


#### Mysql

1. install `Mysql` by the following command
   doc
`brew install mysql`

2. Start the MySQL service

`brew services start mysql`

3. Set root MySQL password
   
`mysql_secure_installation`


4. Access MySQL on mac

`mysql -u root -p`

and fill password:

`password`

5. create database
   
`CREATE DATABASE mysqldb`
`CREATE DATABASE mysqldb CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;`

6. use the database

`mysql -u myuser -p`
`mysql -u root -p`
`password`
`USE mysqldb;`

#### Mssql
https://builtin.com/software-engineering-perspectives/sql-server-management-studio-mac
CREATE DATABASE mssqldb
mssql -u sa -p reallyStrongPwd123
USE mssqldb


docker pull mcr.microsoft.com/mssql/server:2022-latest

docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=reallyStrongPwd123" \
   -p 1433:1433 --name sql1 --hostname sql1 \
   -d \
   mcr.microsoft.com/mssql/server:2022-latest


how to connect?
brew install unixodbc

https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver16

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql17 mssql-tools

#### Oracle
https://cloud.tencent.com/developer/article/1852042
1. docker pull oracleinanutshell/oracle-xe-11g
docker run -d -p 1521:1521 -p 8080:8080 --name oracle oracleinanutshell/oracle-xe-11g
docker exec -it oracle /bin/bash
su - oracle 
sqlplus / as sysdba
create user myuser identified by password;
grant connect,resource,create session to myuser;
grant unlimited tablespace to myuser;
2. 
docker exec -it oracle /bin/bash
su - oracle 
sqlplus / as sysdba
CONNECT myuser/password
commit;

3. how to connect?
https://blog.csdn.net/Fecker/article/details/117067321
1) download https://download.oracle.com/otn_software/mac/instantclient/198000/instantclient-basic-macos.x64-19.8.0.0.0dbru.dmg
2) double click 
3) copy the files to: /usr/local/lib (finder, right click, go to the file folder)


new:
docker pull gvenzl/oracle-free:latest
docker run -d -p 1521:1521 --name oracle-db -e ORACLE_PASSWORD=password gvenzl/oracle-free:latest
sqlplus / as sysdba
create user myuser identified by password;
-- 切换到正确的 PDB（如果需要）
ALTER SESSION SET CONTAINER = FREEPDB1;
-- 授予 CREATE SESSION 权限
GRANT CREATE SESSION TO MYUSER;
-- 同时授予其他常用权限
GRANT CONNECT, RESOURCE TO MYUSER;
-- 如果需要更多权限
GRANT UNLIMITED TABLESPACE TO MYUSER;
-- 提交并退出
COMMIT;
EXIT;

docker exec -it oracle-db /bin/bash 
sqlplus / as sysdba
CONNECT myuser/password



### read sql
mysql -u myuser -p mysqldb < datas_simple_mysql.sql
sqlite3 mydatabase.db < datas_simple.sql
psql -d interpreter -U myuser -W < datas_simple.sql


#### combine into one docker


################################ virtual box ###########
# mysql
https://www.geeksforgeeks.org/how-to-install-mysql-on-linux/
https://medium.com/techvblogs/how-to-reset-mysql-root-password-in-ubuntu-53b05eadbad6

sudo mysql -u root -p
password
USE mysqldb;


# sqlite3
/home/database/mydatabase.db

# postgres

# mssql
sqlcmd -No -S localhost -U sa -P reallyStrongPwd123




#### how to run my python 

1. py_Interpreter ywj$ source venv/bin/activate
2. test ywj$ PYTHONPATH=../ pytest test_sqlite.py 

source activate py39


ubuntu20.04



MSSQL: EXEC sp_columns
MYSQL: DESCRIBE TA



python env:
https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/

mysql docker:
https://medium.com/@maravondra/mysql-in-docker-d7bb1e304473




driver:
oracle(oracle instant client)
https://csiandal.medium.com/install-oracle-instant-client-on-ubuntu-4ffc8fdfda08


cd /opt/
sudo mkdir /opt/oracle
sudo wget https://download.oracle.com/otn_software/linux/instantclient/214000/instantclient-basic-linux.x64-21.4.0.0.0dbru.zip
sudo unzip instantclient_21_4
sudo apt update
sudo apt install libaio1
sudo sh -c "echo /opt/oracle/instantclient_21_4 > /etc/ld.so.conf.d/oracle-instantclient.conf"
sudo ldconfig

mssql:
https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver16&tabs=alpine18-install%2Calpine17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline





SELECT CAST(TA.height AS CHAR) AS col0, CAST(TA.name AS DECIMAL(10,1)) + CAST(TA.name AS DECIMAL(10,1)) AS col1 FROM TA TA 
INTERSECT 
SELECT TB0.fullname AS col0, TA1.age AS col1 FROM TB TB0,TA TA1;








