BEGIN;

CREATE TABLE accounts (
       custid BIGINT      NOT NULL PRIMARY KEY,
       name VARCHAR(255) NOT NULL
);

INSERT INTO accounts VALUES (1, 'Brown');
INSERT INTO accounts VALUES (2, 'Wang');
INSERT INTO accounts VALUES (3, 'O''mahony');
INSERT INTO accounts VALUES (4, 'Weeks');
INSERT INTO accounts VALUES (5, 'Granger');
INSERT INTO accounts VALUES (6, 'Porter');
INSERT INTO accounts VALUES (7, 'Wesley');

CREATE TABLE checking (
       custid BIGINT      NOT NULL PRIMARY KEY,
       balance FLOAT       NOT NULL
);

INSERT INTO checking VALUES (1, 10000.0);
INSERT INTO checking VALUES (2, 2000.0);
INSERT INTO checking VALUES (3, 3000.0);
INSERT INTO checking VALUES (4, 7000.0);
INSERT INTO checking VALUES (5, 10000.0);
INSERT INTO checking VALUES (6, 77.0);
INSERT INTO checking VALUES (7, 7.0);

CREATE TABLE savings (
       custid BIGINT      NOT NULL PRIMARY KEY,
       balance FLOAT       NOT NULL
);

INSERT INTO savings VALUES (1, 200000.0);
INSERT INTO savings VALUES (2, 999999999.0);
INSERT INTO savings VALUES (3, 230000.0);
INSERT INTO savings VALUES (4, 60.0);
INSERT INTO savings VALUES (5, 80000.0);
INSERT INTO savings VALUES (6, 240.0);

COMMIT;