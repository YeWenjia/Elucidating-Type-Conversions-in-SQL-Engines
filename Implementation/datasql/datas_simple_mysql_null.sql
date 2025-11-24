create table TA(name varchar(255), height decimal(10,1), age int);
create table TB(realage int, fullname varchar(255), fullheight decimal(10,1));
create table TC(newage int, newheight decimal(10,1), newname varchar(255));

INSERT INTO TA(name, height, age) VALUES ('Lucas Davis', 6.1, NULL);
INSERT INTO TA(name, height, age) VALUES ('John Doe', 5.8, 30);
INSERT INTO TA(name, height, age) VALUES ('Jane Smith', -5.5, 25);
INSERT INTO TA(name, height, age) VALUES ('Michael Johnson', 6.2, 35);
INSERT INTO TA(name, height, age) VALUES ('David Wilson', 5.1, -32);

INSERT INTO TB(realage, fullname, fullheight) VALUES(-28, 'Emily Davis', 5.9);
INSERT INTO TB(realage, fullname, fullheight) VALUES(32, 'David Wilson', 5.1);
INSERT INTO TB(realage, fullname, fullheight) VALUES(27, 'Sarah Brown', NULL);
INSERT INTO TB(realage, fullname, fullheight) VALUES(29, 'Matthew Lee', 5.2);
INSERT INTO TB(realage, fullname, fullheight) VALUES(32, 'Lucas Parker', 6.1);

INSERT INTO TC(newage, newheight, newname) VALUES(35, 6.2, 'Michael Johnson');
INSERT INTO TC(newage, newheight, newname) VALUES(28, -5.9, 'Emily Davis');
INSERT INTO TC(newage, newheight, newname) VALUES(32, 5.1, 'David Wilson');
INSERT INTO TC(newage, newheight, newname) VALUES(-32, 6.1, 'Lucas Parker');
INSERT INTO TC(newage, newheight, newname) VALUES(27, 5.6, NULL);
