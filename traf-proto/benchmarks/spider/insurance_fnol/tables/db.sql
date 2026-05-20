BEGIN;

CREATE TABLE available_policies (
       policy_id INTEGER NOT NULL,
       policy_type_code VARCHAR(255),
       customer_phone VARCHAR(255),
       primary KEY (policy_id),
       unique (Policy_ID)
);

INSERT INTO available_policies VALUES (246, 'Life Insurance', '+16(2)5838999222');
INSERT INTO available_policies VALUES (257, 'Property Insurance', '242.763.9214');
INSERT INTO available_policies VALUES (300, 'Property Insurance', '1-416-503-7735x94204');
INSERT INTO available_policies VALUES (301, 'Property Insurance', '(777)537-7792');
INSERT INTO available_policies VALUES (346, 'Mortgage Insurance', '1-446-940-9907x257');
INSERT INTO available_policies VALUES (366, 'Mortgage Insurance', '(379)862-8274x12620');
INSERT INTO available_policies VALUES (472, 'Mortgage Insurance', '+85(6)1302858396');
INSERT INTO available_policies VALUES (583, 'Travel Insurance', '1-797-927-3585x9321');
INSERT INTO available_policies VALUES (586, 'Life Insurance', '991.642.6485x822');
INSERT INTO available_policies VALUES (630, 'Property Insurance', '813.178.8211x557');
INSERT INTO available_policies VALUES (636, 'Life Insurance', '889-572-0609x552');
INSERT INTO available_policies VALUES (751, 'Life Insurance', '1-138-841-3073');
INSERT INTO available_policies VALUES (879, 'Mortgage Insurance', '1-381-132-0127x3801');
INSERT INTO available_policies VALUES (927, 'Mortgage Insurance', '00481937923');
INSERT INTO available_policies VALUES (993, 'Property Insurance', '405.090.8654x021');

CREATE TABLE claims (
       claim_id INTEGER NOT NULL,
       fnol_id INTEGER NOT NULL,
       effective_date DATE,
       primary KEY (claim_id),
       unique (Claim_ID)
);

INSERT INTO claims VALUES (134, 1722, '1973-08-18');
INSERT INTO claims VALUES (145, 1611, '2014-10-19');
INSERT INTO claims VALUES (228, 532, '1975-05-07');
INSERT INTO claims VALUES (309, 2543, '1982-05-03');
INSERT INTO claims VALUES (311, 4226, '1992-02-09');
INSERT INTO claims VALUES (360, 4226, '2006-06-10');
INSERT INTO claims VALUES (428, 4226, '1992-01-05');
INSERT INTO claims VALUES (604, 4323, '2009-02-11');
INSERT INTO claims VALUES (641, 4525, '1985-03-24');
INSERT INTO claims VALUES (717, 4525, '1996-11-29');

CREATE TABLE customers (
       customer_id INTEGER NOT NULL,
       customer_name VARCHAR(255),
       primary KEY (customer_id)
);

INSERT INTO customers VALUES (194, 'America Jaskolski');
INSERT INTO customers VALUES (214, 'Ellsworth Paucek');
INSERT INTO customers VALUES (256, 'Mrs. Hanna Willms');
INSERT INTO customers VALUES (562, 'Dr. Diana Rath');
INSERT INTO customers VALUES (582, 'Selena Gerhold');
INSERT INTO customers VALUES (641, 'Dayana Robel');
INSERT INTO customers VALUES (682, 'Mr. Edwardo Blanda I');
INSERT INTO customers VALUES (756, 'Mr. Randal Lynch III');
INSERT INTO customers VALUES (805, 'Mrs. Liza Heller V');
INSERT INTO customers VALUES (826, 'Mrs. Lilly Graham III');
INSERT INTO customers VALUES (882, 'Miss Felicita Reichel');
INSERT INTO customers VALUES (892, 'Sydnie Friesen');
INSERT INTO customers VALUES (923, 'David Ross');
INSERT INTO customers VALUES (956, 'Cai Zhang');
INSERT INTO customers VALUES (996, 'Jay Chou');

CREATE TABLE customers_policies (
       customer_id INTEGER NOT NULL,
       policy_id INTEGER NOT NULL,
       date_opened DATE,
       date_closed DATE,
       primary KEY (customer_id, policy_id)
);

INSERT INTO customers_policies VALUES (214, 257, '2016-11-19', '2018-03-04');
INSERT INTO customers_policies VALUES (214, 301, '2016-04-12', '2018-02-07');
INSERT INTO customers_policies VALUES (256, 583, '2016-07-22', '2018-02-20');
INSERT INTO customers_policies VALUES (562, 346, '2017-01-09', '2018-03-08');
INSERT INTO customers_policies VALUES (562, 583, '2016-06-24', '2018-02-22');
INSERT INTO customers_policies VALUES (582, 586, '2016-04-11', '2018-03-17');
INSERT INTO customers_policies VALUES (641, 366, '2016-07-10', '2018-02-24');
INSERT INTO customers_policies VALUES (641, 472, '2016-07-07', '2018-03-10');
INSERT INTO customers_policies VALUES (682, 583, '2016-11-01', '2018-03-03');
INSERT INTO customers_policies VALUES (826, 630, '2016-11-18', '2018-02-13');
INSERT INTO customers_policies VALUES (892, 927, '2017-01-08', '2018-02-25');
INSERT INTO customers_policies VALUES (996, 366, '2016-10-31', '2018-03-19');
INSERT INTO customers_policies VALUES (996, 879, '2017-01-05', '2018-02-20');
INSERT INTO customers_policies VALUES (996, 993, '2016-07-03', '2018-03-20');

CREATE TABLE first_notification_of_loss (
       fnol_id INTEGER NOT NULL,
       customer_id INTEGER NOT NULL,
       policy_id INTEGER NOT NULL,
       service_id INTEGER NOT NULL,
       primary KEY (fnol_id),
       unique (FNOL_ID)
);

INSERT INTO first_notification_of_loss VALUES (532, 214, 257, 6);
INSERT INTO first_notification_of_loss VALUES (1611, 996, 993, 9);
INSERT INTO first_notification_of_loss VALUES (1722, 996, 879, 6);
INSERT INTO first_notification_of_loss VALUES (2543, 996, 366, 1);
INSERT INTO first_notification_of_loss VALUES (4226, 892, 927, 1);
INSERT INTO first_notification_of_loss VALUES (4323, 826, 630, 4);
INSERT INTO first_notification_of_loss VALUES (4525, 582, 586, 1);

CREATE TABLE services (
       service_id INTEGER NOT NULL,
       service_name VARCHAR(255),
       primary KEY (service_id)
);

INSERT INTO services VALUES (1, 'New policy application');
INSERT INTO services VALUES (4, 'Close a policy');
INSERT INTO services VALUES (6, 'Change a policy');
INSERT INTO services VALUES (9, 'Upgrade a policy');

CREATE TABLE settlements (
       settlement_id INTEGER NOT NULL,
       claim_id INTEGER,
       effective_date DATE,
       settlement_amount REAL,
       primary KEY (settlement_id),
       unique (Settlement_ID)
);

INSERT INTO settlements VALUES (161, 717, '2009-11-20', 6451.65);
INSERT INTO settlements VALUES (176, 641, '1971-06-29', 1588.45);
INSERT INTO settlements VALUES (205, 604, '1978-09-09', 9814.39);
INSERT INTO settlements VALUES (208, 428, '2003-12-28', 8827.06);
INSERT INTO settlements VALUES (393, 360, '2006-04-19', 8013.95);
INSERT INTO settlements VALUES (543, 309, '1972-03-02', 2722.67);
INSERT INTO settlements VALUES (544, 311, '1973-10-27', 9164.1);
INSERT INTO settlements VALUES (604, 228, '2014-12-09', 2138.96);
INSERT INTO settlements VALUES (616, 145, '1995-04-02', 3101.3);
INSERT INTO settlements VALUES (628, 134, '2001-07-02', 1721.17);

COMMIT;