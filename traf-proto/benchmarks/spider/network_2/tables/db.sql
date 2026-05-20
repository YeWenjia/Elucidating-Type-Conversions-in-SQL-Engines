BEGIN;

CREATE TABLE person (
       name VARCHAR(255) PRIMARY KEY,
       age INTEGER,
       city TEXT,
       gender TEXT,
       job TEXT
);

INSERT INTO person VALUES ('Alice', 25, 'new york city', 'female', 'student');
INSERT INTO person VALUES ('Bob', 35, 'salt lake city', 'male', 'engineer');
INSERT INTO person VALUES ('Zach', 45, 'austin', 'male', 'doctor');
INSERT INTO person VALUES ('Dan', 26, 'chicago', 'female', 'student');

CREATE TABLE personfriend (
       name VARCHAR(255),
       friend VARCHAR(255),
       year INTEGER
);

INSERT INTO personfriend VALUES ('Alice', 'Bob', 10);
INSERT INTO personfriend VALUES ('Zach', 'Dan', 12);
INSERT INTO personfriend VALUES ('Bob', 'Zach', 5);
INSERT INTO personfriend VALUES ('Zach', 'Alice', 6);

COMMIT;