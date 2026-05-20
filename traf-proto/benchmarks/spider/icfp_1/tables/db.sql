BEGIN;

CREATE TABLE authors (
       authid INTEGER,
       lname TEXT,
       fname TEXT,
       primary KEY (authid)
);

INSERT INTO authors VALUES (50, 'Gibbons', 'Jeremy');
INSERT INTO authors VALUES (51, 'Hinze', 'Ralf');
INSERT INTO authors VALUES (52, 'James', 'Daniel W. H.');
INSERT INTO authors VALUES (53, 'Shivers', 'Olin');
INSERT INTO authors VALUES (54, 'Turon', 'Aaron');
INSERT INTO authors VALUES (55, 'Ahmed', 'Amal');
INSERT INTO authors VALUES (56, 'Blume', 'Matthias');
INSERT INTO authors VALUES (57, 'Ohori', 'Atsushi');
INSERT INTO authors VALUES (58, 'Ueno', 'Katsuhiro');
INSERT INTO authors VALUES (59, 'Pouillard', 'Nicolas');
INSERT INTO authors VALUES (60, 'Weirich', 'Stephanie');
INSERT INTO authors VALUES (61, 'Yorgey', 'Brent');
INSERT INTO authors VALUES (62, 'Sheard', 'Tim');

CREATE TABLE authorship (
       authid INTEGER,
       instid INTEGER,
       paperid INTEGER,
       authorder INTEGER,
       primary KEY (authid, instid, paperid)
);

INSERT INTO authorship VALUES (50, 1000, 200, 1);
INSERT INTO authorship VALUES (51, 1000, 200, 2);
INSERT INTO authorship VALUES (51, 1000, 201, 1);
INSERT INTO authorship VALUES (52, 1000, 201, 2);
INSERT INTO authorship VALUES (53, 1010, 202, 1);
INSERT INTO authorship VALUES (54, 1010, 202, 2);
INSERT INTO authorship VALUES (55, 1020, 203, 1);
INSERT INTO authorship VALUES (56, 1030, 203, 2);
INSERT INTO authorship VALUES (57, 1040, 204, 1);
INSERT INTO authorship VALUES (58, 1040, 204, 2);
INSERT INTO authorship VALUES (59, 1070, 205, 1);
INSERT INTO authorship VALUES (60, 1050, 206, 1);
INSERT INTO authorship VALUES (61, 1050, 206, 2);
INSERT INTO authorship VALUES (62, 1060, 206, 3);

CREATE TABLE inst (
       instid INTEGER,
       name TEXT,
       country TEXT,
       primary KEY (instid)
);

INSERT INTO inst VALUES (1000, 'University of Oxford', 'UK');
INSERT INTO inst VALUES (1010, 'Northeastern University', 'USA');
INSERT INTO inst VALUES (1020, 'Indiana University', 'USA');
INSERT INTO inst VALUES (1030, 'Google', 'USA');
INSERT INTO inst VALUES (1040, 'Tohoku University', 'Japan');
INSERT INTO inst VALUES (1050, 'University of Pennsylvania', 'USA');
INSERT INTO inst VALUES (1060, 'Portland State University', 'Japan');
INSERT INTO inst VALUES (1070, 'INRIA', 'France');

CREATE TABLE papers (
       paperid INTEGER,
       title TEXT,
       primary KEY (paperid)
);

INSERT INTO papers VALUES (200, 'Just do it: Simple Monadic Equational Reasoning');
INSERT INTO papers VALUES (201, 'Proving the Unique Fixed-Point Principle Correct: An Adventure with Category Theory');
INSERT INTO papers VALUES (202, 'Functional Pearl: Modular Rollback through Control Logging');
INSERT INTO papers VALUES (203, 'An Equivalence-Preserving CPS Translation via Multi-Language Semantics');
INSERT INTO papers VALUES (204, 'Making Standard ML a Practical Database Programming Language');
INSERT INTO papers VALUES (205, 'Nameless, Painless');
INSERT INTO papers VALUES (206, 'Binders Unbound');

COMMIT;