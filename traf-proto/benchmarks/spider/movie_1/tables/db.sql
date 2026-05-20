BEGIN;

CREATE TABLE movie (
       mid int primary key,
       title text,
       year int,
       director text
);

INSERT INTO movie VALUES (101, 'Gone with the Wind', 1939, 'Victor Fleming');
INSERT INTO movie VALUES (102, 'Star Wars', 1977, 'George Lucas');
INSERT INTO movie VALUES (103, 'The Sound of Music', 1965, 'Robert Wise');
INSERT INTO movie VALUES (104, 'E.T.', 1982, 'Steven Spielberg');
INSERT INTO movie VALUES (105, 'Titanic', 1997, 'James Cameron');
INSERT INTO movie VALUES (106, 'Snow White', 1937, NULL);
INSERT INTO movie VALUES (107, 'Avatar', 2009, 'James Cameron');
INSERT INTO movie VALUES (108, 'Raiders of the Lost Ark', 1981, 'Steven Spielberg');

CREATE TABLE rating (
       rid int,
       mid int,
       stars int,
       ratingdate date
);

INSERT INTO rating VALUES (201, 101, 2, '2011-01-22');
INSERT INTO rating VALUES (201, 101, 4, '2011-01-27');
INSERT INTO rating VALUES (202, 106, 4, NULL);
INSERT INTO rating VALUES (203, 103, 2, '2011-01-20');
INSERT INTO rating VALUES (203, 108, 4, '2011-01-12');
INSERT INTO rating VALUES (203, 108, 2, '2011-01-30');
INSERT INTO rating VALUES (204, 101, 3, '2011-01-09');
INSERT INTO rating VALUES (205, 103, 3, '2011-01-27');
INSERT INTO rating VALUES (205, 104, 2, '2011-01-22');
INSERT INTO rating VALUES (205, 108, 4, NULL);
INSERT INTO rating VALUES (206, 107, 3, '2011-01-15');
INSERT INTO rating VALUES (206, 106, 5, '2011-01-19');
INSERT INTO rating VALUES (207, 107, 5, '2011-01-20');
INSERT INTO rating VALUES (208, 104, 3, '2011-01-02');

CREATE TABLE reviewer (
       rid int primary key,
       name text
);

INSERT INTO reviewer VALUES (201, 'Sarah Martinez');
INSERT INTO reviewer VALUES (202, 'Daniel Lewis');
INSERT INTO reviewer VALUES (203, 'Brittany Harris');
INSERT INTO reviewer VALUES (204, 'Mike Anderson');
INSERT INTO reviewer VALUES (205, 'Chris Jackson');
INSERT INTO reviewer VALUES (206, 'Elizabeth Thomas');
INSERT INTO reviewer VALUES (207, 'James Cameron');
INSERT INTO reviewer VALUES (208, 'Ashley White');

COMMIT;