BEGIN;

CREATE TABLE dorm (
       dormid INTEGER,
       dorm_name VARCHAR(255),
       student_capacity INTEGER,
       gender VARCHAR(255)
);

INSERT INTO dorm VALUES (100, 'Smith Hall', 85, 'X');
INSERT INTO dorm VALUES (110, 'Bud Jones Hall', 116, 'M');
INSERT INTO dorm VALUES (140, 'Fawlty Towers', 355, 'X');
INSERT INTO dorm VALUES (160, 'Dorm-plex 2000', 400, 'X');
INSERT INTO dorm VALUES (109, 'Anonymous Donor Hall', 128, 'F');
INSERT INTO dorm VALUES (117, 'University Hovels', 40, 'X');
INSERT INTO dorm VALUES (104, 'Grad Student Asylum', 256, 'X');

CREATE TABLE dorm_amenity (
       amenid INTEGER,
       amenity_name VARCHAR(255)
);

INSERT INTO dorm_amenity VALUES (900, 'TV Lounge');
INSERT INTO dorm_amenity VALUES (901, 'Study Room');
INSERT INTO dorm_amenity VALUES (902, 'Pub in Basement');
INSERT INTO dorm_amenity VALUES (903, 'Carpeted Rooms');
INSERT INTO dorm_amenity VALUES (904, '4 Walls');
INSERT INTO dorm_amenity VALUES (930, 'Roof');
INSERT INTO dorm_amenity VALUES (931, 'Ethernet Ports');
INSERT INTO dorm_amenity VALUES (932, 'Air Conditioning');
INSERT INTO dorm_amenity VALUES (922, 'Heat');
INSERT INTO dorm_amenity VALUES (950, 'Working Fireplaces');
INSERT INTO dorm_amenity VALUES (955, 'Kitchen in Every Room');
INSERT INTO dorm_amenity VALUES (909, 'Allows Pets');

CREATE TABLE has_amenity (
       dormid INTEGER,
       amenid INTEGER
);

INSERT INTO has_amenity VALUES (109, 900);
INSERT INTO has_amenity VALUES (109, 901);
INSERT INTO has_amenity VALUES (109, 903);
INSERT INTO has_amenity VALUES (109, 904);
INSERT INTO has_amenity VALUES (109, 930);
INSERT INTO has_amenity VALUES (109, 931);
INSERT INTO has_amenity VALUES (109, 932);
INSERT INTO has_amenity VALUES (109, 922);
INSERT INTO has_amenity VALUES (104, 901);
INSERT INTO has_amenity VALUES (104, 904);
INSERT INTO has_amenity VALUES (104, 930);
INSERT INTO has_amenity VALUES (160, 900);
INSERT INTO has_amenity VALUES (160, 901);
INSERT INTO has_amenity VALUES (160, 902);
INSERT INTO has_amenity VALUES (160, 903);
INSERT INTO has_amenity VALUES (160, 931);
INSERT INTO has_amenity VALUES (160, 904);
INSERT INTO has_amenity VALUES (160, 930);
INSERT INTO has_amenity VALUES (160, 922);
INSERT INTO has_amenity VALUES (160, 932);
INSERT INTO has_amenity VALUES (160, 950);
INSERT INTO has_amenity VALUES (160, 955);
INSERT INTO has_amenity VALUES (160, 909);
INSERT INTO has_amenity VALUES (100, 901);
INSERT INTO has_amenity VALUES (100, 903);
INSERT INTO has_amenity VALUES (100, 904);
INSERT INTO has_amenity VALUES (100, 930);
INSERT INTO has_amenity VALUES (100, 922);
INSERT INTO has_amenity VALUES (117, 930);
INSERT INTO has_amenity VALUES (110, 901);
INSERT INTO has_amenity VALUES (110, 903);
INSERT INTO has_amenity VALUES (110, 904);
INSERT INTO has_amenity VALUES (110, 930);
INSERT INTO has_amenity VALUES (110, 922);
INSERT INTO has_amenity VALUES (140, 909);
INSERT INTO has_amenity VALUES (140, 900);
INSERT INTO has_amenity VALUES (140, 902);
INSERT INTO has_amenity VALUES (140, 904);
INSERT INTO has_amenity VALUES (140, 930);
INSERT INTO has_amenity VALUES (140, 932);

CREATE TABLE lives_in (
       stuid INTEGER,
       dormid INTEGER,
       room_number INTEGER
);

INSERT INTO lives_in VALUES (1001, 109, 105);
INSERT INTO lives_in VALUES (1002, 100, 112);
INSERT INTO lives_in VALUES (1003, 100, 124);
INSERT INTO lives_in VALUES (1004, 140, 215);
INSERT INTO lives_in VALUES (1005, 160, 333);
INSERT INTO lives_in VALUES (1007, 140, 113);
INSERT INTO lives_in VALUES (1008, 160, 334);
INSERT INTO lives_in VALUES (1009, 140, 332);
INSERT INTO lives_in VALUES (1010, 160, 443);
INSERT INTO lives_in VALUES (1011, 140, 102);
INSERT INTO lives_in VALUES (1012, 160, 333);
INSERT INTO lives_in VALUES (1014, 104, 211);
INSERT INTO lives_in VALUES (1015, 160, 443);
INSERT INTO lives_in VALUES (1016, 140, 301);
INSERT INTO lives_in VALUES (1017, 140, 319);
INSERT INTO lives_in VALUES (1018, 140, 225);
INSERT INTO lives_in VALUES (1020, 160, 405);
INSERT INTO lives_in VALUES (1021, 160, 405);
INSERT INTO lives_in VALUES (1022, 100, 153);
INSERT INTO lives_in VALUES (1023, 160, 317);
INSERT INTO lives_in VALUES (1024, 100, 151);
INSERT INTO lives_in VALUES (1025, 160, 317);
INSERT INTO lives_in VALUES (1027, 140, 208);
INSERT INTO lives_in VALUES (1028, 110, 48);
INSERT INTO lives_in VALUES (1029, 140, 418);
INSERT INTO lives_in VALUES (1030, 109, 211);
INSERT INTO lives_in VALUES (1031, 100, 112);
INSERT INTO lives_in VALUES (1032, 109, 105);
INSERT INTO lives_in VALUES (1033, 117, 3);
INSERT INTO lives_in VALUES (1034, 160, 105);
INSERT INTO lives_in VALUES (1035, 100, 124);

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

COMMIT;