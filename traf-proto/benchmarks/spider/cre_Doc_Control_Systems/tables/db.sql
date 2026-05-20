BEGIN;

CREATE TABLE addresses (
       address_id INTEGER NOT NULL,
       address_details VARCHAR(255),
       primary KEY (address_id)
);

INSERT INTO addresses VALUES (0, 'IT');
INSERT INTO addresses VALUES (1, 'MX');
INSERT INTO addresses VALUES (2, 'DE');
INSERT INTO addresses VALUES (3, 'ES');
INSERT INTO addresses VALUES (4, 'ES');
INSERT INTO addresses VALUES (5, 'IE');
INSERT INTO addresses VALUES (6, 'US');
INSERT INTO addresses VALUES (7, 'PT');
INSERT INTO addresses VALUES (8, 'IE');
INSERT INTO addresses VALUES (9, 'MX');

CREATE TABLE circulation_history (
       document_id INTEGER NOT NULL,
       draft_number INTEGER NOT NULL,
       copy_number INTEGER NOT NULL,
       employee_id INTEGER NOT NULL,
       primary KEY (document_id, draft_number, copy_number, employee_id)
);

INSERT INTO circulation_history VALUES (20, 17, 15, 8);
INSERT INTO circulation_history VALUES (1, 2, 5, 1);
INSERT INTO circulation_history VALUES (2, 1, 4, 2);
INSERT INTO circulation_history VALUES (10, 20, 10, 2);

CREATE TABLE document_drafts (
       document_id INTEGER NOT NULL,
       draft_number INTEGER NOT NULL,
       draft_details VARCHAR(255),
       primary KEY (document_id, draft_number)
);

INSERT INTO document_drafts VALUES (1, 0, 'e');
INSERT INTO document_drafts VALUES (1, 2, 'k');
INSERT INTO document_drafts VALUES (2, 1, 'v');
INSERT INTO document_drafts VALUES (2, 8, 'v');
INSERT INTO document_drafts VALUES (4, 9, 'r');
INSERT INTO document_drafts VALUES (7, 10, 'm');
INSERT INTO document_drafts VALUES (10, 20, 'k');
INSERT INTO document_drafts VALUES (12, 11, 'b');
INSERT INTO document_drafts VALUES (12, 12, 'r');
INSERT INTO document_drafts VALUES (13, 4, 'w');
INSERT INTO document_drafts VALUES (13, 16, 'p');
INSERT INTO document_drafts VALUES (14, 14, 'x');
INSERT INTO document_drafts VALUES (17, 19, 'a');
INSERT INTO document_drafts VALUES (20, 17, 'l');
INSERT INTO document_drafts VALUES (23, 9, 'r');

CREATE TABLE documents (
       document_id INTEGER NOT NULL,
       document_status_code VARCHAR(255) NOT NULL,
       document_type_code VARCHAR(255) NOT NULL,
       shipping_agent_code VARCHAR(255),
       receipt_date TIMESTAMP,
       receipt_number VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (document_id)
);

INSERT INTO documents VALUES (1, 'working', 'CD', 'UP', '2008-04-21 20:42:25', '19', 'z');
INSERT INTO documents VALUES (2, 'done', 'Paper', 'US', '1974-05-08 00:00:46', '34', 'h');
INSERT INTO documents VALUES (3, 'done', 'Paper', 'UP', '2014-12-25 17:22:44', '93', 'h');
INSERT INTO documents VALUES (4, 'done', 'Paper', 'US', '1973-11-05 21:48:53', '80', 'q');
INSERT INTO documents VALUES (7, 'working', 'CD', 'SH', '1982-09-27 14:52:15', '61', 'w');
INSERT INTO documents VALUES (10, 'overdue', 'Paper', 'UP', '1976-09-15 19:24:17', '8', 'm');
INSERT INTO documents VALUES (12, 'overdue', 'Hard Drive', 'US', '1996-05-31 06:51:58', '69', 'n');
INSERT INTO documents VALUES (13, 'working', 'CD', 'UP', '2015-04-03 09:36:19', '79', 'y');
INSERT INTO documents VALUES (14, 'working', 'CD', 'FE', '2017-07-02 17:39:09', '117', 'u');
INSERT INTO documents VALUES (15, 'overdue', 'CD', 'UP', '1986-12-14 14:18:59', '37', 'r');
INSERT INTO documents VALUES (17, 'done', 'Paper', 'FE', '1983-09-26 09:32:56', '55', 'p');
INSERT INTO documents VALUES (20, 'working', 'Paper', 'UP', '1996-07-27 03:30:40', '189', 'x');
INSERT INTO documents VALUES (23, 'working', 'Hard Drive', 'FE', '1999-04-17 14:19:32', '124', 'b');
INSERT INTO documents VALUES (24, 'working', 'Hard Drive', 'FE', '2005-09-30 00:10:02', '114', 'j');
INSERT INTO documents VALUES (25, 'overdue', 'Hard Drive', 'AL', '1985-11-05 17:59:34', '83', 'u');

CREATE TABLE documents_mailed (
       document_id INTEGER NOT NULL,
       mailed_to_address_id INTEGER NOT NULL,
       mailing_date TIMESTAMP,
       primary KEY (document_id, mailed_to_address_id)
);

INSERT INTO documents_mailed VALUES (2, 8, '1977-04-01 17:03:50');
INSERT INTO documents_mailed VALUES (4, 3, '1992-11-07 15:03:41');
INSERT INTO documents_mailed VALUES (4, 9, '1973-02-21 10:17:01');
INSERT INTO documents_mailed VALUES (7, 5, '1979-09-21 10:30:52');
INSERT INTO documents_mailed VALUES (10, 3, '1993-05-24 22:13:48');
INSERT INTO documents_mailed VALUES (12, 0, '1999-05-22 23:21:07');
INSERT INTO documents_mailed VALUES (12, 7, '2007-01-01 22:32:11');
INSERT INTO documents_mailed VALUES (12, 8, '2007-03-20 05:22:01');
INSERT INTO documents_mailed VALUES (13, 4, '1991-05-27 14:17:37');
INSERT INTO documents_mailed VALUES (14, 5, '1986-05-16 06:25:33');
INSERT INTO documents_mailed VALUES (20, 2, '2010-11-04 04:00:16');
INSERT INTO documents_mailed VALUES (20, 7, '1982-01-14 05:50:54');
INSERT INTO documents_mailed VALUES (23, 8, '1971-11-03 12:32:14');
INSERT INTO documents_mailed VALUES (24, 0, '2013-01-27 03:29:31');

CREATE TABLE draft_copies (
       document_id INTEGER NOT NULL,
       draft_number INTEGER NOT NULL,
       copy_number INTEGER NOT NULL,
       primary KEY (document_id, draft_number, copy_number)
);

INSERT INTO draft_copies VALUES (2, 8, 5);
INSERT INTO draft_copies VALUES (4, 9, 6);
INSERT INTO draft_copies VALUES (23, 9, 15);
INSERT INTO draft_copies VALUES (10, 20, 10);
INSERT INTO draft_copies VALUES (2, 1, 4);
INSERT INTO draft_copies VALUES (1, 2, 5);
INSERT INTO draft_copies VALUES (20, 17, 15);
INSERT INTO draft_copies VALUES (12, 12, 10);

CREATE TABLE employees (
       employee_id INTEGER NOT NULL,
       role_code VARCHAR(255) NOT NULL,
       employee_name VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (employee_id)
);

INSERT INTO employees VALUES (1, 'ED', 'Koby', 'h');
INSERT INTO employees VALUES (2, 'ED', 'Kenyon', 'f');
INSERT INTO employees VALUES (3, 'PR', 'Haley', 'b');
INSERT INTO employees VALUES (5, 'PT', 'Clemens', 'b');
INSERT INTO employees VALUES (7, 'PT', 'Jordyn', 'v');
INSERT INTO employees VALUES (8, 'MG', 'Erling', 'u');

CREATE TABLE ref_document_status (
       document_status_code VARCHAR(255) NOT NULL,
       document_status_description VARCHAR(255) NOT NULL,
       primary KEY (document_status_code)
);

INSERT INTO ref_document_status VALUES ('working', 'currently working on');
INSERT INTO ref_document_status VALUES ('done', 'mailed');
INSERT INTO ref_document_status VALUES ('overdue', 'mailed late');

CREATE TABLE ref_document_types (
       document_type_code VARCHAR(255) NOT NULL,
       document_type_description VARCHAR(255) NOT NULL,
       primary KEY (document_type_code)
);

INSERT INTO ref_document_types VALUES ('CD', 'b');
INSERT INTO ref_document_types VALUES ('Paper', 'u');
INSERT INTO ref_document_types VALUES ('Hard Drive', 'f');

CREATE TABLE ref_shipping_agents (
       shipping_agent_code VARCHAR(255) NOT NULL,
       shipping_agent_name VARCHAR(255) NOT NULL,
       shipping_agent_description VARCHAR(255) NOT NULL,
       primary KEY (shipping_agent_code)
);

INSERT INTO ref_shipping_agents VALUES ('UP', 'UPS', 'g');
INSERT INTO ref_shipping_agents VALUES ('US', 'USPS', 'q');
INSERT INTO ref_shipping_agents VALUES ('AL', 'Airline', 'w');
INSERT INTO ref_shipping_agents VALUES ('FE', 'Fedex', 'k');
INSERT INTO ref_shipping_agents VALUES ('SH', 'Ship', 't');

CREATE TABLE roles (
       role_code VARCHAR(255) NOT NULL,
       role_description VARCHAR(255),
       primary KEY (role_code)
);

INSERT INTO roles VALUES ('ED', 'Editor');
INSERT INTO roles VALUES ('PT', 'Photo');
INSERT INTO roles VALUES ('MG', 'Manager');
INSERT INTO roles VALUES ('PR', 'Proof Manager');

COMMIT;