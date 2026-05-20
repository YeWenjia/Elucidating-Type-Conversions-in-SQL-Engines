BEGIN;

CREATE TABLE plays_games (
       stuid INTEGER,
       gameid INTEGER,
       hours_played INTEGER
);

INSERT INTO plays_games VALUES (1001, 1, 35);
INSERT INTO plays_games VALUES (1001, 2, 15);
INSERT INTO plays_games VALUES (1001, 5, 1);
INSERT INTO plays_games VALUES (1007, 4, 1000);
INSERT INTO plays_games VALUES (1008, 5, 50);
INSERT INTO plays_games VALUES (1008, 3, 50);
INSERT INTO plays_games VALUES (1010, 6, 1337);
INSERT INTO plays_games VALUES (1032, 1, 47);
INSERT INTO plays_games VALUES (1032, 2, 10);
INSERT INTO plays_games VALUES (1032, 3, 100);

CREATE TABLE sportsinfo (
       stuid INTEGER,
       sportname VARCHAR(255),
       hoursperweek INTEGER,
       gamesplayed INTEGER,
       onscholarship VARCHAR(255)
);

INSERT INTO sportsinfo VALUES (1001, 'Athletics', 2, 5, 'N');
INSERT INTO sportsinfo VALUES (1002, 'Football', 7, 20, 'Y');
INSERT INTO sportsinfo VALUES (1003, 'Football', 45, 18, 'Y');
INSERT INTO sportsinfo VALUES (1005, 'Lacrosse', 35, 16, 'N');
INSERT INTO sportsinfo VALUES (1015, 'Lacrosse', 25, 41, 'Y');
INSERT INTO sportsinfo VALUES (1018, 'Lacrosse', 39, 25, 'N');
INSERT INTO sportsinfo VALUES (1019, 'Swimming', 8, 16, 'Y');
INSERT INTO sportsinfo VALUES (1019, 'Tennis', 19, 62, 'N');
INSERT INTO sportsinfo VALUES (1022, 'Baseball', 29, 31, 'N');
INSERT INTO sportsinfo VALUES (1023, 'Basketball', 14, 8, 'Y');
INSERT INTO sportsinfo VALUES (1023, 'Tennis', 1, 56, 'Y');
INSERT INTO sportsinfo VALUES (1026, 'Cricket', 23, 37, 'Y');
INSERT INTO sportsinfo VALUES (1033, 'Soccer', 45, 45, 'Y');
INSERT INTO sportsinfo VALUES (1035, 'Curling', 50, 94, 'N');

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

CREATE TABLE video_games (
       gameid INTEGER PRIMARY KEY,
       gname VARCHAR(255),
       gtype VARCHAR(255)
);

INSERT INTO video_games VALUES (1, 'RNG Stone', 'Collectible card game');
INSERT INTO video_games VALUES (2, 'The Vanishing of Eric Calder', 'Walking Simulator');
INSERT INTO video_games VALUES (3, 'Grand Term Assignment', 'Role-playing game');
INSERT INTO video_games VALUES (4, 'Europe is the Universe', 'Grand strategy');
INSERT INTO video_games VALUES (5, 'Call of Destiny', 'Frist-person shooter');
INSERT INTO video_games VALUES (6, 'Works of Widenius', 'Massively multiplayer online game');

COMMIT;