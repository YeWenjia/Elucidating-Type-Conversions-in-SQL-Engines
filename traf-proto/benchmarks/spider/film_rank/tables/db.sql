BEGIN;

CREATE TABLE film (
       "film_id" int,
       "title" text,
       "studio" text,
       "director" text,
       "gross_in_dollar" int,
       primary KEY (film_id)
);

INSERT INTO film VALUES (1, 'ET the Extra-Terrestrial', 'Universal', 'Steven Spielberg', 435110554);
INSERT INTO film VALUES (2, 'Tootsie', 'Columbia', 'Sydney Pollack', 177200000);
INSERT INTO film VALUES (3, 'An Officer and a Gentleman', 'Paramount / Lorimar', 'Taylor Hackford', 129795554);
INSERT INTO film VALUES (4, 'Rocky III', 'United Artists', 'Sylvester Stallone', 125049125);
INSERT INTO film VALUES (5, 'Porky''s', '20th Century Fox', 'Bob Clark', 109492484);
INSERT INTO film VALUES (6, 'Star Trek II: The Wrath of Khan', 'Paramount', 'Nicholas Meyer', 79912963);
INSERT INTO film VALUES (7, '48 Hrs', 'Paramount', 'Walter Hill', 78868508);
INSERT INTO film VALUES (8, 'Poltergeist', 'MGM', 'Tobe Hooper', 76606280);
INSERT INTO film VALUES (9, 'The Best Little Whorehouse in Texas', 'Universal / RKO', 'Colin Higgins', 69701637);
INSERT INTO film VALUES (10, 'Annie', 'Columbia / Rastar', 'John Huston', 57059003);
INSERT INTO film VALUES (11, 'The Verdict', '20th Century Fox', 'Sidney Lumet', 53977250);
INSERT INTO film VALUES (12, 'Gandhi', 'Columbia', 'Richard Attenborough', 52767889);
INSERT INTO film VALUES (13, 'First Blood', 'Orion / Carolco', 'Ted Kotcheff', 47212904);

CREATE TABLE film_market_estimation (
       "estimation_id" int,
       "low_estimate" real,
       "high_estimate" real,
       "film_id" int,
       "type" text,
       "market_id" int,
       "year" int,
       primary KEY (estimation_id)
);

INSERT INTO film_market_estimation VALUES (1, 80000.0, 80400.0, 1, 'Mass suicide murder', 1, 1945);
INSERT INTO film_market_estimation VALUES (2, 8000.0, 8000.0, 2, 'Mass suicide', 2, 1944);
INSERT INTO film_market_estimation VALUES (3, 3000.0, 80400.0, 3, 'Mass human sacrifice', 3, 1487);
INSERT INTO film_market_estimation VALUES (4, 960.0, 960.0, 4, 'Mass suicide', 2, 1973);
INSERT INTO film_market_estimation VALUES (5, 913.0, 913.0, 4, 'Mass suicide murder', 1, 1978);
INSERT INTO film_market_estimation VALUES (6, 300.0, 1000.0, 4, 'Mass suicide', 1, 2000);
INSERT INTO film_market_estimation VALUES (7, 53.0, 53.0, 4, 'Mass suicide', 1, 1994);
INSERT INTO film_market_estimation VALUES (8, 39.0, 39.0, 1, 'Mass suicide', 2, 1997);
INSERT INTO film_market_estimation VALUES (9, 16.0, 16.0, 1, 'Mass suicide', 3, 1995);

CREATE TABLE market (
       "market_id" int,
       "country" text,
       "number_cities" int,
       primary KEY (market_id)
);

INSERT INTO market VALUES (1, 'Japan', 209);
INSERT INTO market VALUES (2, 'China', 540);
INSERT INTO market VALUES (3, 'USA', 700);
INSERT INTO market VALUES (4, 'Russia', 231);
INSERT INTO market VALUES (5, 'France', 212);
INSERT INTO market VALUES (6, 'Poland', 453);

COMMIT;