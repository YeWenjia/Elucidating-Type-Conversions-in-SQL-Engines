# A Formal Framework for Typing and Cast Semantics in SQL Engines

We recommend using PyCharm to run. 

1. install python3.12 and select it as the environment in PyCharm.

2. install packages in `requirements.txt`.

3. install the DBMS (Sqlite, Mysql, Postgresql, Mssql, Oracle) in the local computer.

4. create tables in different engines as in `datasql` folder, note that file name with `_null` means that there is null value.  

4. fill in the username, password ... in configuration file `config.yml` which is located at `../Implementation/test/mytesting/config.yml`.

5. run tests `psql_testing.py`, `mysql_testing.py`, `sqlite_testing.py`, `mssql_testing.py`, `oracle_testing.py` in folder `../Implementation/test/mytesting`.

Please note that folder `Implementation` supports for Exists, In and NULL while `MyInterpreter` does not.











