BEGIN;

CREATE TABLE benefits_overpayments (
       council_tax_id INTEGER NOT NULL,
       cmi_cross_ref_id INTEGER NOT NULL,
       primary KEY (council_tax_id)
);

INSERT INTO benefits_overpayments VALUES (3, 65);
INSERT INTO benefits_overpayments VALUES (6, 41);
INSERT INTO benefits_overpayments VALUES (7, 83);
INSERT INTO benefits_overpayments VALUES (8, 48);

CREATE TABLE business_rates (
       business_rates_id INTEGER NOT NULL,
       cmi_cross_ref_id INTEGER NOT NULL,
       primary KEY (business_rates_id)
);

INSERT INTO business_rates VALUES (2, 99);
INSERT INTO business_rates VALUES (5, 49);
INSERT INTO business_rates VALUES (8, 95);

CREATE TABLE cmi_cross_references (
       cmi_cross_ref_id INTEGER NOT NULL,
       master_customer_id INTEGER NOT NULL,
       source_system_code VARCHAR(255) NOT NULL,
       primary KEY (cmi_cross_ref_id)
);

INSERT INTO cmi_cross_references VALUES (2, 4, 'Rent');
INSERT INTO cmi_cross_references VALUES (4, 5, 'Parking');
INSERT INTO cmi_cross_references VALUES (8, 1, 'Rent');
INSERT INTO cmi_cross_references VALUES (41, 5, 'Benefits');
INSERT INTO cmi_cross_references VALUES (48, 5, 'Benefits');
INSERT INTO cmi_cross_references VALUES (49, 1, 'Business');
INSERT INTO cmi_cross_references VALUES (59, 1, 'Rent');
INSERT INTO cmi_cross_references VALUES (65, 9, 'Benefits');
INSERT INTO cmi_cross_references VALUES (75, 5, 'Electoral');
INSERT INTO cmi_cross_references VALUES (77, 4, 'Electoral');
INSERT INTO cmi_cross_references VALUES (81, 9, 'Parking');
INSERT INTO cmi_cross_references VALUES (83, 3, 'Benefits');
INSERT INTO cmi_cross_references VALUES (95, 2, 'Business');
INSERT INTO cmi_cross_references VALUES (99, 9, 'Business');
INSERT INTO cmi_cross_references VALUES (100, 4, 'Rent');
INSERT INTO cmi_cross_references VALUES (101, 2, 'Tax');
INSERT INTO cmi_cross_references VALUES (102, 4, 'Tax');
INSERT INTO cmi_cross_references VALUES (103, 9, 'Tax');
INSERT INTO cmi_cross_references VALUES (104, 2, 'Tax');
INSERT INTO cmi_cross_references VALUES (105, 2, 'Tax');
INSERT INTO cmi_cross_references VALUES (106, 1, 'Tax');

CREATE TABLE council_tax (
       council_tax_id INTEGER NOT NULL,
       cmi_cross_ref_id INTEGER NOT NULL,
       primary KEY (council_tax_id)
);

INSERT INTO council_tax VALUES (1, 101);
INSERT INTO council_tax VALUES (2, 103);
INSERT INTO council_tax VALUES (3, 104);
INSERT INTO council_tax VALUES (7, 102);
INSERT INTO council_tax VALUES (8, 106);
INSERT INTO council_tax VALUES (9, 105);

CREATE TABLE customer_master_index (
       master_customer_id INTEGER NOT NULL,
       cmi_details VARCHAR(255),
       primary KEY (master_customer_id)
);

INSERT INTO customer_master_index VALUES (1, 'Schmitt-Lang');
INSERT INTO customer_master_index VALUES (2, 'Volkman, Mills and Ferry');
INSERT INTO customer_master_index VALUES (3, 'Gusikowski PLC');
INSERT INTO customer_master_index VALUES (4, 'Schmidt, Kertzmann and Lubowitz');
INSERT INTO customer_master_index VALUES (5, 'Gottlieb, Becker and Wyman');
INSERT INTO customer_master_index VALUES (6, 'Mayer-Hagenes');
INSERT INTO customer_master_index VALUES (7, 'Streich-Morissette');
INSERT INTO customer_master_index VALUES (8, 'Quigley-Paucek');
INSERT INTO customer_master_index VALUES (9, 'Reynolds-McClure');

CREATE TABLE electoral_register (
       electoral_register_id INTEGER NOT NULL,
       cmi_cross_ref_id INTEGER NOT NULL,
       primary KEY (electoral_register_id)
);

INSERT INTO electoral_register VALUES (2, 83);
INSERT INTO electoral_register VALUES (3, 65);
INSERT INTO electoral_register VALUES (4, 100);
INSERT INTO electoral_register VALUES (6, 95);
INSERT INTO electoral_register VALUES (7, 65);
INSERT INTO electoral_register VALUES (8, 75);

CREATE TABLE parking_fines (
       council_tax_id INTEGER NOT NULL,
       cmi_cross_ref_id INTEGER NOT NULL,
       primary KEY (council_tax_id)
);

INSERT INTO parking_fines VALUES (9, 4);
INSERT INTO parking_fines VALUES (10, 81);

CREATE TABLE rent_arrears (
       council_tax_id INTEGER NOT NULL,
       cmi_cross_ref_id INTEGER NOT NULL,
       primary KEY (council_tax_id)
);

INSERT INTO rent_arrears VALUES (1, 100);
INSERT INTO rent_arrears VALUES (2, 8);
INSERT INTO rent_arrears VALUES (6, 59);
INSERT INTO rent_arrears VALUES (7, 2);

COMMIT;