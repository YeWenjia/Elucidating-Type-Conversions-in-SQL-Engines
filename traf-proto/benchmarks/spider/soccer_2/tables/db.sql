BEGIN;

CREATE TABLE college (
       cname VARCHAR(255) NOT NULL,
       state VARCHAR(255),
       enr numeric(5,0),
       primary KEY (cname)
);

INSERT INTO college VALUES ('LSU', 'LA', 18000);
INSERT INTO college VALUES ('ASU', 'AZ', 12000);
INSERT INTO college VALUES ('OU', 'OK', 22000);
INSERT INTO college VALUES ('FSU', 'FL', 19000);

CREATE TABLE player (
       pid numeric(5,0) NOT NULL,
       pname VARCHAR(255),
       ycard VARCHAR(255),
       hs numeric(5,0),
       primary KEY (pid)
);

INSERT INTO player VALUES (10001, 'Andrew', 'no', 1200);
INSERT INTO player VALUES (20002, 'Blake', 'no', 1600);
INSERT INTO player VALUES (30003, 'Charles', 'no', 300);
INSERT INTO player VALUES (40004, 'David', 'yes', 1600);
INSERT INTO player VALUES (40002, 'Drago', 'yes', 1600);
INSERT INTO player VALUES (50005, 'Eddie', 'yes', 600);

CREATE TABLE tryout (
       pid numeric(5,0),
       cname VARCHAR(255),
       ppos VARCHAR(255),
       decision VARCHAR(255),
       primary KEY (pid, cname)
);

INSERT INTO tryout VALUES (10001, 'LSU', 'goalie', 'no');
INSERT INTO tryout VALUES (10001, 'ASU', 'goalie', 'yes');
INSERT INTO tryout VALUES (20002, 'FSU', 'striker', 'yes');
INSERT INTO tryout VALUES (30003, 'OU', 'mid', 'no');
INSERT INTO tryout VALUES (40004, 'ASU', 'goalie', 'no');
INSERT INTO tryout VALUES (50005, 'LSU', 'mid', 'no');

COMMIT;