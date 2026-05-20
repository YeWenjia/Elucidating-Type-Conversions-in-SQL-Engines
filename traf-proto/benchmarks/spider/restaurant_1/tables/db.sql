BEGIN;

CREATE TABLE restaurant (
       resid INTEGER PRIMARY KEY,
       resname VARCHAR(255),
       address VARCHAR(255),
       rating INTEGER
);

INSERT INTO restaurant VALUES (1, 'Subway', '3233 St Paul St, Baltimore, MD 21218', 3);
INSERT INTO restaurant VALUES (2, 'Honeygrow', '3212 St Paul St, Baltimore, MD 21218', 4);

CREATE TABLE restaurant_type (
       restypeid INTEGER PRIMARY KEY,
       restypename VARCHAR(255),
       restypedescription VARCHAR(255)
);

INSERT INTO restaurant_type VALUES (1, 'Sandwich', 'Simplest there is.');
INSERT INTO restaurant_type VALUES (2, 'Stir-fry', 'Classic Chinese cooking.');

CREATE TABLE student (
       stuid INTEGER PRIMARY KEY,
       lname VARCHAR(255),
       fname VARCHAR(255),
       age INTEGER,
       sex VARCHAR(255),
       major INTEGER,
       advisor INTEGER,
       city_code VARCHAR(255)
);

INSERT INTO student VALUES (1001, 'Smith', 'Linda', 18, 'F', 600, 1121, 'BAL');
INSERT INTO student VALUES (1002, 'Kim', 'Tracy', 19, 'F', 600, 7712, 'HKG');
INSERT INTO student VALUES (1003, 'Jones', 'Shiela', 21, 'F', 600, 7792, 'WAS');
INSERT INTO student VALUES (1004, 'Kumar', 'Dinesh', 20, 'M', 600, 8423, 'CHI');
INSERT INTO student VALUES (1005, 'Gompers', 'Paul', 26, 'M', 600, 1121, 'YYZ');
INSERT INTO student VALUES (1006, 'Schultz', 'Andy', 18, 'M', 600, 1148, 'BAL');
INSERT INTO student VALUES (1007, 'Apap', 'Lisa', 18, 'F', 600, 8918, 'PIT');
INSERT INTO student VALUES (1008, 'Nelson', 'Jandy', 20, 'F', 600, 9172, 'BAL');
INSERT INTO student VALUES (1009, 'Tai', 'Eric', 19, 'M', 600, 2192, 'YYZ');
INSERT INTO student VALUES (1010, 'Lee', 'Derek', 17, 'M', 600, 2192, 'HOU');
INSERT INTO student VALUES (1011, 'Adams', 'David', 22, 'M', 600, 1148, 'PHL');
INSERT INTO student VALUES (1012, 'Davis', 'Steven', 20, 'M', 600, 7723, 'PIT');
INSERT INTO student VALUES (1014, 'Norris', 'Charles', 18, 'M', 600, 8741, 'DAL');
INSERT INTO student VALUES (1015, 'Lee', 'Susan', 16, 'F', 600, 8721, 'HKG');
INSERT INTO student VALUES (1016, 'Schwartz', 'Mark', 17, 'M', 600, 2192, 'DET');
INSERT INTO student VALUES (1017, 'Wilson', 'Bruce', 27, 'M', 600, 1148, 'LON');
INSERT INTO student VALUES (1018, 'Leighton', 'Michael', 20, 'M', 600, 1121, 'PIT');
INSERT INTO student VALUES (1019, 'Pang', 'Arthur', 18, 'M', 600, 2192, 'WAS');
INSERT INTO student VALUES (1020, 'Thornton', 'Ian', 22, 'M', 520, 7271, 'NYC');
INSERT INTO student VALUES (1021, 'Andreou', 'George', 19, 'M', 520, 8722, 'NYC');
INSERT INTO student VALUES (1022, 'Woods', 'Michael', 17, 'M', 540, 8722, 'PHL');
INSERT INTO student VALUES (1023, 'Shieber', 'David', 20, 'M', 520, 8722, 'NYC');
INSERT INTO student VALUES (1024, 'Prater', 'Stacy', 18, 'F', 540, 7271, 'BAL');
INSERT INTO student VALUES (1025, 'Goldman', 'Mark', 18, 'M', 520, 7134, 'PIT');
INSERT INTO student VALUES (1026, 'Pang', 'Eric', 19, 'M', 520, 7134, 'HKG');
INSERT INTO student VALUES (1027, 'Brody', 'Paul', 18, 'M', 520, 8723, 'LOS');
INSERT INTO student VALUES (1028, 'Rugh', 'Eric', 20, 'M', 550, 2311, 'ROC');
INSERT INTO student VALUES (1029, 'Han', 'Jun', 17, 'M', 100, 2311, 'PEK');
INSERT INTO student VALUES (1030, 'Cheng', 'Lisa', 21, 'F', 550, 2311, 'SFO');
INSERT INTO student VALUES (1031, 'Smith', 'Sarah', 20, 'F', 550, 8772, 'PHL');
INSERT INTO student VALUES (1032, 'Brown', 'Eric', 20, 'M', 550, 8772, 'ATL');
INSERT INTO student VALUES (1033, 'Simms', 'William', 18, 'M', 550, 8772, 'NAR');
INSERT INTO student VALUES (1034, 'Epp', 'Eric', 18, 'M', 50, 5718, 'BOS');
INSERT INTO student VALUES (1035, 'Schmidt', 'Sarah', 26, 'F', 50, 5718, 'WAS');

CREATE TABLE type_of_restaurant (
       resid INTEGER,
       restypeid INTEGER
);

INSERT INTO type_of_restaurant VALUES (1, 1);
INSERT INTO type_of_restaurant VALUES (2, 2);

CREATE TABLE visits_restaurant (
       stuid INTEGER,
       resid INTEGER,
       time TIMESTAMP,
       spent FLOAT
);

INSERT INTO visits_restaurant VALUES (1001, 1, '2017-10-09 18:15:00', 6.53);
INSERT INTO visits_restaurant VALUES (1032, 2, '2017-10-08 13:00:30', 13.2);

COMMIT;