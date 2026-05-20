BEGIN;

CREATE TABLE happy_hour (
       "hh_id" int,
       "shop_id" int,
       "month" text,
       "num_of_shaff_in_charge" int,
       primary KEY (hh_id, shop_id, month)
);

INSERT INTO happy_hour VALUES (1, 1, 'May', 10);
INSERT INTO happy_hour VALUES (2, 1, 'April', 12);
INSERT INTO happy_hour VALUES (3, 10, 'June', 15);
INSERT INTO happy_hour VALUES (4, 5, 'July', 5);
INSERT INTO happy_hour VALUES (5, 1, 'May', 10);
INSERT INTO happy_hour VALUES (6, 1, 'April', 12);
INSERT INTO happy_hour VALUES (7, 2, 'June', 5);
INSERT INTO happy_hour VALUES (8, 3, 'July', 15);
INSERT INTO happy_hour VALUES (9, 3, 'May', 3);
INSERT INTO happy_hour VALUES (10, 3, 'April', 4);

CREATE TABLE happy_hour_member (
       "hh_id" int,
       "member_id" int,
       "total_amount" real,
       primary KEY (hh_id, member_id)
);

INSERT INTO happy_hour_member VALUES (1, 3, 20.9);
INSERT INTO happy_hour_member VALUES (4, 3, 20.92);
INSERT INTO happy_hour_member VALUES (7, 9, 4.9);
INSERT INTO happy_hour_member VALUES (2, 5, 16.9);
INSERT INTO happy_hour_member VALUES (5, 5, 16.92);
INSERT INTO happy_hour_member VALUES (8, 9, 4.2);

CREATE TABLE member (
       "member_id" int,
       "name" text,
       "membership_card" text,
       "age" int,
       "time_of_purchase" int,
       "level_of_membership" int,
       "address" text,
       primary KEY (member_id)
);

INSERT INTO member VALUES (1, 'Ashby, Lazale', 'Black', 29, 18, 5, 'Hartford');
INSERT INTO member VALUES (2, 'Breton, Robert', 'White', 67, 41, 4, 'Waterbury');
INSERT INTO member VALUES (3, 'Campbell, Jessie', 'Black', 34, 20, 6, 'Hartford');
INSERT INTO member VALUES (4, 'Cobb, Sedrick', 'Black', 51, 27, 2, 'Waterbury');
INSERT INTO member VALUES (5, 'Hayes, Steven', 'White', 50, 44, 3, 'Cheshire');
INSERT INTO member VALUES (6, 'Komisarjevsky, Joshua', 'White', 33, 26, 2, 'Cheshire');
INSERT INTO member VALUES (7, 'Peeler, Russell', 'Black', 42, 26, 6, 'Bridgeport');
INSERT INTO member VALUES (8, 'Reynolds, Richard', 'Black', 45, 24, 1, 'Waterbury');
INSERT INTO member VALUES (9, 'Rizzo, Todd', 'White', 35, 18, 4, 'Waterbury');
INSERT INTO member VALUES (10, 'Webb, Daniel', 'Black', 51, 27, 22, 'Hartford');

CREATE TABLE shop (
       "shop_id" int,
       "address" text,
       "num_of_staff" text,
       "score" real,
       "open_year" text,
       primary KEY (shop_id)
);

INSERT INTO shop VALUES (1, '1200 Main Street', '13', 42.0, '2010');
INSERT INTO shop VALUES (2, '1111 Main Street', '19', 38.0, '2008');
INSERT INTO shop VALUES (3, '1330 Baltimore Street', '42', 36.0, '2010');
INSERT INTO shop VALUES (4, '909 Walnut Street', '27', 32.0, '2010');
INSERT INTO shop VALUES (5, '414 E. 12th Street', '24', 30.0, '2011');
INSERT INTO shop VALUES (6, '1201 Walnut Street', '34', 30.0, '2010');
INSERT INTO shop VALUES (7, '2345 McGee Street', '425', 40.0, '2008');
INSERT INTO shop VALUES (8, '909 Main Street', '28', 30.0, '2011');
INSERT INTO shop VALUES (9, '1100 Main Street', '23', 30.0, '2006');
INSERT INTO shop VALUES (10, '324 E. 11th Street', '16', 28.0, '2008');

COMMIT;