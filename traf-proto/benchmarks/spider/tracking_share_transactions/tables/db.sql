BEGIN;

CREATE TABLE investors (
       `investor_id` INTEGER PRIMARY KEY,
       `investor_details` VARCHAR(255)
);

INSERT INTO investors VALUES (1, 'z');
INSERT INTO investors VALUES (2, 'z');
INSERT INTO investors VALUES (3, 'd');
INSERT INTO investors VALUES (4, 'd');
INSERT INTO investors VALUES (5, 'b');
INSERT INTO investors VALUES (6, 'k');
INSERT INTO investors VALUES (7, 'l');
INSERT INTO investors VALUES (8, 't');
INSERT INTO investors VALUES (9, 'y');
INSERT INTO investors VALUES (10, 'r');
INSERT INTO investors VALUES (11, 'q');
INSERT INTO investors VALUES (12, 'c');
INSERT INTO investors VALUES (13, 'o');
INSERT INTO investors VALUES (14, 'w');
INSERT INTO investors VALUES (15, 'i');
INSERT INTO investors VALUES (16, 'y');
INSERT INTO investors VALUES (17, 'k');
INSERT INTO investors VALUES (18, 'w');
INSERT INTO investors VALUES (19, 'l');
INSERT INTO investors VALUES (20, 'j');

CREATE TABLE lots (
       `lot_id` INTEGER PRIMARY KEY,
       `investor_id` INTEGER NOT NULL,
       `lot_details` VARCHAR(255)
);

INSERT INTO lots VALUES (1, 13, 'r');
INSERT INTO lots VALUES (2, 16, 'z');
INSERT INTO lots VALUES (3, 10, 's');
INSERT INTO lots VALUES (4, 19, 's');
INSERT INTO lots VALUES (5, 6, 'q');
INSERT INTO lots VALUES (6, 20, 'd');
INSERT INTO lots VALUES (7, 7, 'm');
INSERT INTO lots VALUES (8, 7, 'h');
INSERT INTO lots VALUES (9, 20, 'z');
INSERT INTO lots VALUES (10, 9, 'x');
INSERT INTO lots VALUES (11, 1, 'd');
INSERT INTO lots VALUES (12, 19, 'm');
INSERT INTO lots VALUES (13, 7, 'z');
INSERT INTO lots VALUES (14, 6, 'd');
INSERT INTO lots VALUES (15, 1, 'h');

CREATE TABLE purchases (
       `purchase_transaction_id` INTEGER NOT NULL,
       `purchase_details` VARCHAR(255) NOT NULL
);

INSERT INTO purchases VALUES (1, 'c');
INSERT INTO purchases VALUES (2, 'y');
INSERT INTO purchases VALUES (3, 'i');
INSERT INTO purchases VALUES (4, 'x');
INSERT INTO purchases VALUES (5, 'y');
INSERT INTO purchases VALUES (6, 'a');
INSERT INTO purchases VALUES (7, 'r');
INSERT INTO purchases VALUES (8, 'a');
INSERT INTO purchases VALUES (9, 'r');
INSERT INTO purchases VALUES (10, 'l');
INSERT INTO purchases VALUES (11, 'z');
INSERT INTO purchases VALUES (12, 'h');
INSERT INTO purchases VALUES (13, 't');
INSERT INTO purchases VALUES (14, 'o');
INSERT INTO purchases VALUES (15, 'x');

CREATE TABLE ref_transaction_types (
       `transaction_type_code` VARCHAR(255) PRIMARY KEY,
       `transaction_type_description` VARCHAR(255) NOT NULL
);

INSERT INTO ref_transaction_types VALUES ('SALE', 'Sale');
INSERT INTO ref_transaction_types VALUES ('PUR', 'Purchase');

CREATE TABLE sales (
       `sales_transaction_id` INTEGER PRIMARY KEY,
       `sales_details` VARCHAR(255)
);

INSERT INTO sales VALUES (1, 'x');
INSERT INTO sales VALUES (2, 'o');
INSERT INTO sales VALUES (3, 'a');
INSERT INTO sales VALUES (4, 'f');
INSERT INTO sales VALUES (5, 'y');
INSERT INTO sales VALUES (6, 'x');
INSERT INTO sales VALUES (7, 'p');
INSERT INTO sales VALUES (8, 'e');
INSERT INTO sales VALUES (9, 'p');
INSERT INTO sales VALUES (10, 's');
INSERT INTO sales VALUES (11, 's');
INSERT INTO sales VALUES (12, 't');
INSERT INTO sales VALUES (13, 'p');
INSERT INTO sales VALUES (14, 'n');
INSERT INTO sales VALUES (15, 'e');

CREATE TABLE transactions (
       `transaction_id` INTEGER PRIMARY KEY,
       `investor_id` INTEGER NOT NULL,
       `transaction_type_code` VARCHAR(255) NOT NULL,
       `date_of_transaction` TIMESTAMP,
       `amount_of_transaction` DECIMAL(19,4),
       `share_count` VARCHAR(255),
       `other_details` VARCHAR(255)
);

INSERT INTO transactions VALUES (1, 6, 'SALE', '1988-09-16 19:02:51', 302507.6996, '8718572', NULL);
INSERT INTO transactions VALUES (2, 18, 'PUR', '1982-06-06 17:19:00', 27.257, '9', NULL);
INSERT INTO transactions VALUES (3, 2, 'SALE', '1979-04-27 06:03:59', 48777.969, '8580', NULL);
INSERT INTO transactions VALUES (4, 14, 'PUR', '2001-11-28 15:06:25', 4.5263, '8040', NULL);
INSERT INTO transactions VALUES (5, 8, 'PUR', '1977-08-17 13:13:30', 0, '930', NULL);
INSERT INTO transactions VALUES (6, 19, 'PUR', '1985-10-08 13:13:39', 207484122.2796, '2751', NULL);
INSERT INTO transactions VALUES (7, 7, 'PUR', '1990-12-02 09:03:38', 822.803, '1522', NULL);
INSERT INTO transactions VALUES (8, 17, 'SALE', '2004-01-18 20:37:50', 78035671.4424, '96178', NULL);
INSERT INTO transactions VALUES (9, 20, 'PUR', '1977-08-13 02:18:47', 82057.207, '', NULL);
INSERT INTO transactions VALUES (10, 2, 'SALE', '1981-01-28 08:07:03', 29.3534, '1654756', NULL);
INSERT INTO transactions VALUES (11, 3, 'SALE', '2000-04-03 20:55:43', 0, '674529892', NULL);
INSERT INTO transactions VALUES (12, 18, 'SALE', '1983-11-01 17:57:27', 1, '587', NULL);
INSERT INTO transactions VALUES (13, 3, 'SALE', '2002-04-07 20:28:37', 183.2, '', NULL);
INSERT INTO transactions VALUES (14, 3, 'PUR', '2002-09-13 03:04:56', 0, '630021', NULL);
INSERT INTO transactions VALUES (15, 19, 'PUR', '1997-12-30 05:05:40', 8.9, '93191', NULL);

CREATE TABLE transactions_lots (
       `transaction_id` INTEGER NOT NULL,
       `lot_id` INTEGER NOT NULL
);

INSERT INTO transactions_lots VALUES (3, 11);
INSERT INTO transactions_lots VALUES (3, 8);
INSERT INTO transactions_lots VALUES (2, 11);
INSERT INTO transactions_lots VALUES (3, 14);
INSERT INTO transactions_lots VALUES (12, 10);
INSERT INTO transactions_lots VALUES (15, 10);
INSERT INTO transactions_lots VALUES (10, 10);
INSERT INTO transactions_lots VALUES (1, 1);
INSERT INTO transactions_lots VALUES (1, 14);
INSERT INTO transactions_lots VALUES (3, 4);
INSERT INTO transactions_lots VALUES (14, 9);
INSERT INTO transactions_lots VALUES (7, 1);
INSERT INTO transactions_lots VALUES (12, 15);
INSERT INTO transactions_lots VALUES (6, 3);
INSERT INTO transactions_lots VALUES (2, 1);

COMMIT;