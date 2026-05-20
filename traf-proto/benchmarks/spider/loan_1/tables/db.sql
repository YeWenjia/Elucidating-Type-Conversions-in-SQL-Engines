BEGIN;

CREATE TABLE bank (
       branch_id int PRIMARY KEY,
       bname VARCHAR(255),
       no_of_customers int,
       city VARCHAR(255),
       state VARCHAR(255)
);

INSERT INTO bank VALUES (1, 'morningside', 203, 'New York City', 'New York');
INSERT INTO bank VALUES (2, 'downtown', 123, 'Salt Lake City', 'Utah');
INSERT INTO bank VALUES (3, 'broadway', 453, 'New York City', 'New York');
INSERT INTO bank VALUES (4, 'high', 367, 'Austin', 'Texas');

CREATE TABLE customer (
       cust_id VARCHAR(255) PRIMARY KEY,
       cust_name VARCHAR(255),
       acc_type VARCHAR(255),
       acc_bal int,
       no_of_loans int,
       credit_score int,
       branch_id int,
       state VARCHAR(255)
);

INSERT INTO customer VALUES ('1', 'Mary', 'saving', 2000, 2, 30, 2, 'Utah');
INSERT INTO customer VALUES ('2', 'Jack', 'checking', 1000, 1, 20, 1, 'Texas');
INSERT INTO customer VALUES ('3', 'Owen', 'saving', 800000, 0, 210, 3, 'New York');

CREATE TABLE loan (
       loan_id VARCHAR(255) PRIMARY KEY,
       loan_type VARCHAR(255),
       cust_id VARCHAR(255),
       branch_id VARCHAR(255),
       amount int
);

INSERT INTO loan VALUES ('1', 'Mortgages', '1', '1', 2050);
INSERT INTO loan VALUES ('2', 'Auto', '1', '2', 3000);
INSERT INTO loan VALUES ('3', 'Business', '3', '3', 5000);

COMMIT;