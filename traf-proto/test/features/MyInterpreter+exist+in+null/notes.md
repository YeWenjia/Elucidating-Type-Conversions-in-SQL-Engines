psql -d interpreter -U myuser
myuser

mysql -u myuser -p
password
USE mysqldb;

sqlite3 mydatabase.db

mssql -u sa -p reallyStrongPwd123
USE mssqldb

docker exec -it oracle /bin/bash
su - oracle 
sqlplus / as sysdba
CONNECT myuser/password
commit;


select 1 where '1' IN (select 1);
select 1 where exists (select 1 where '1' = 1);

select 1 where '1.1' IN (select 1);
select 1 where exists (select 1 where '1.1' = 1);

select 1 where '1.1' IN (select 1.1);
select 1 where exists (select 1 where '1.1' = 1.1);
