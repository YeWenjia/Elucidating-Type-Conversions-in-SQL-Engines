BEGIN;

CREATE TABLE claims (
       claim_id INTEGER NOT NULL,
       policy_id INTEGER NOT NULL,
       date_claim_made DATE,
       date_claim_settled DATE,
       amount_claimed INTEGER,
       amount_settled INTEGER,
       primary KEY (claim_id)
);

INSERT INTO claims VALUES (143, 744, '2017-03-11', '2017-11-03', 43884, 1085);
INSERT INTO claims VALUES (423, 552, '2016-08-12', '2018-01-27', 79134, 1724);
INSERT INTO claims VALUES (442, 473, '2017-02-24', '2018-01-21', 70088, 1189);
INSERT INTO claims VALUES (486, 141, '2018-06-14', '2017-12-20', 69696, 1638);
INSERT INTO claims VALUES (546, 744, '2017-05-03', '2017-12-22', 46479, 1091);
INSERT INTO claims VALUES (563, 141, '2016-08-02', '2017-09-04', 41078, 1570);
INSERT INTO claims VALUES (569, 473, '2018-07-15', '2017-11-19', 49743, 930);
INSERT INTO claims VALUES (571, 858, '2017-08-03', '2018-02-18', 89632, 1528);
INSERT INTO claims VALUES (621, 744, '2016-12-18', '2018-01-11', 43708, 1652);
INSERT INTO claims VALUES (761, 473, '2016-08-26', '2017-09-04', 83703, 1372);
INSERT INTO claims VALUES (801, 738, '2017-10-21', '2018-01-05', 3326, 1353);
INSERT INTO claims VALUES (843, 143, '2017-10-14', '2018-02-20', 10209, 1639);
INSERT INTO claims VALUES (935, 143, '2018-07-13', '2017-11-22', 70674, 1637);
INSERT INTO claims VALUES (957, 352, '2018-11-08', '2017-09-15', 38280, 1050);
INSERT INTO claims VALUES (965, 119, '2017-07-17', '2018-03-09', 35824, 1636);

CREATE TABLE customer_policies (
       policy_id INTEGER NOT NULL,
       customer_id INTEGER NOT NULL,
       policy_type_code VARCHAR(255) NOT NULL,
       start_date DATE,
       end_date DATE,
       primary KEY (policy_id)
);

INSERT INTO customer_policies VALUES (119, 1, 'Car', '2018-01-21', '2017-12-15');
INSERT INTO customer_policies VALUES (141, 2, 'Life', '2017-08-21', '2017-09-29');
INSERT INTO customer_policies VALUES (143, 3, 'Car', '2017-06-16', '2017-12-09');
INSERT INTO customer_policies VALUES (218, 4, 'Car', '2017-09-18', '2017-11-23');
INSERT INTO customer_policies VALUES (264, 4, 'Car', '2016-12-25', '2018-01-25');
INSERT INTO customer_policies VALUES (270, 5, 'Life', '2016-07-17', '2018-01-05');
INSERT INTO customer_policies VALUES (352, 6, 'Property', '2016-05-23', '2017-12-09');
INSERT INTO customer_policies VALUES (396, 7, 'Travel', '2017-07-30', '2017-10-09');
INSERT INTO customer_policies VALUES (473, 3, 'Travel', '2017-04-24', '2017-12-14');
INSERT INTO customer_policies VALUES (552, 12, 'Travel', '2017-12-13', '2017-11-05');
INSERT INTO customer_policies VALUES (587, 13, 'Travel', '2017-03-23', '2017-09-01');
INSERT INTO customer_policies VALUES (738, 8, 'Travel', '2018-06-16', '2017-12-04');
INSERT INTO customer_policies VALUES (744, 6, 'Property', '2017-12-01', '2018-03-07');
INSERT INTO customer_policies VALUES (858, 9, 'Property', '2016-05-30', '2018-02-11');
INSERT INTO customer_policies VALUES (900, 2, 'Property', '2017-01-20', '2017-12-11');

CREATE TABLE customers (
       customer_id INTEGER NOT NULL,
       customer_details VARCHAR(255) NOT NULL,
       primary KEY (customer_id)
);

INSERT INTO customers VALUES (1, 'America Jaskolski');
INSERT INTO customers VALUES (2, 'Ellsworth Paucek');
INSERT INTO customers VALUES (3, 'Mrs. Hanna Willms');
INSERT INTO customers VALUES (4, 'Dr. Diana Rath');
INSERT INTO customers VALUES (5, 'Selena Gerhold');
INSERT INTO customers VALUES (6, 'Lauriane Ferry PhD');
INSERT INTO customers VALUES (7, 'Sydnie Friesen');
INSERT INTO customers VALUES (8, 'Dayana Robel');
INSERT INTO customers VALUES (9, 'Mr. Edwardo Blanda I');
INSERT INTO customers VALUES (10, 'Augustine Kerluke');
INSERT INTO customers VALUES (11, 'Buddy Marquardt');
INSERT INTO customers VALUES (12, 'Mr. Randal Lynch III');
INSERT INTO customers VALUES (13, 'Mrs. Liza Heller V');
INSERT INTO customers VALUES (14, 'Mrs. Lilly Graham III');
INSERT INTO customers VALUES (15, 'Miss Felicita Reichel');

CREATE TABLE payments (
       payment_id INTEGER NOT NULL,
       settlement_id INTEGER NOT NULL,
       payment_method_code VARCHAR(255),
       date_payment_made DATE,
       amount_payment INTEGER,
       primary KEY (payment_id)
);

INSERT INTO payments VALUES (384, 516, 'MasterCard', '2018-02-16', 241730);
INSERT INTO payments VALUES (435, 476, 'MasterCard', '2017-05-28', 448613);
INSERT INTO payments VALUES (484, 516, 'MasterCard', '2017-06-24', 456098);
INSERT INTO payments VALUES (498, 682, 'Discover Card', '2017-08-06', 38324);
INSERT INTO payments VALUES (542, 597, 'MasterCard', '2018-01-10', 407235);
INSERT INTO payments VALUES (559, 512, 'MasterCard', '2018-02-18', 235893);
INSERT INTO payments VALUES (678, 516, 'Visa', '2017-12-16', 459407);
INSERT INTO payments VALUES (739, 597, 'Discover Card', '2017-10-07', 71246);
INSERT INTO payments VALUES (754, 516, 'Visa', '2018-02-24', 7343);
INSERT INTO payments VALUES (774, 527, 'MasterCard', '2018-01-28', 319142);
INSERT INTO payments VALUES (779, 564, 'Visa', '2017-05-28', 155654);
INSERT INTO payments VALUES (791, 983, 'Visa', '2017-05-03', 172309);
INSERT INTO payments VALUES (886, 516, 'MasterCard', '2017-07-31', 423154);
INSERT INTO payments VALUES (912, 648, 'Discover Card', '2017-05-04', 123255);
INSERT INTO payments VALUES (983, 682, 'American Express', '2018-01-19', 177130);

CREATE TABLE settlements (
       settlement_id INTEGER NOT NULL,
       claim_id INTEGER NOT NULL,
       date_claim_made DATE,
       date_claim_settled DATE,
       amount_claimed INTEGER,
       amount_settled INTEGER,
       customer_policy_id INTEGER NOT NULL,
       primary KEY (settlement_id)
);

INSERT INTO settlements VALUES (357, 486, '2018-08-07', '2018-01-16', 38543, 1181, 515);
INSERT INTO settlements VALUES (412, 621, '2017-08-27', '2018-02-04', 57669, 1427, 617);
INSERT INTO settlements VALUES (476, 801, '2016-09-05', '2018-03-02', 30954, 1805, 943);
INSERT INTO settlements VALUES (512, 801, '2016-05-18', '2018-02-11', 82506, 1737, 133);
INSERT INTO settlements VALUES (516, 563, '2017-05-19', '2017-10-06', 37302, 1767, 638);
INSERT INTO settlements VALUES (527, 801, '2018-11-10', '2018-02-15', 25078, 930, 727);
INSERT INTO settlements VALUES (558, 569, '2018-05-12', '2017-11-30', 16603, 1516, 536);
INSERT INTO settlements VALUES (564, 761, '2016-07-04', '2018-02-20', 62680, 1676, 839);
INSERT INTO settlements VALUES (597, 486, '2017-04-18', '2017-12-24', 4456, 1698, 359);
INSERT INTO settlements VALUES (616, 957, '2017-07-31', '2018-01-27', 24055, 1262, 590);
INSERT INTO settlements VALUES (648, 761, '2017-09-22', '2018-02-14', 32079, 1266, 805);
INSERT INTO settlements VALUES (682, 801, '2017-03-04', '2018-02-20', 56850, 1508, 564);
INSERT INTO settlements VALUES (756, 571, '2017-04-14', '2017-11-15', 8634, 1293, 448);
INSERT INTO settlements VALUES (897, 843, '2017-03-29', '2018-02-20', 20569, 1885, 678);
INSERT INTO settlements VALUES (983, 621, '2016-07-19', '2017-11-04', 3864, 1042, 419);

COMMIT;