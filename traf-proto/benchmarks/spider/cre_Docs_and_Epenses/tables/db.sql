BEGIN;

CREATE TABLE accounts (
       account_id INTEGER NOT NULL,
       statement_id INTEGER NOT NULL,
       account_details VARCHAR(255),
       primary KEY (account_id)
);

INSERT INTO accounts VALUES (7, 57, '495.063');
INSERT INTO accounts VALUES (61, 57, '930.14');
INSERT INTO accounts VALUES (98, 57, '6035.84');
INSERT INTO accounts VALUES (136, 57, '199.52');
INSERT INTO accounts VALUES (164, 192, '12223.93');
INSERT INTO accounts VALUES (209, 57, '11130.23');
INSERT INTO accounts VALUES (211, 192, '1230.454');
INSERT INTO accounts VALUES (240, 192, '6352.31');
INSERT INTO accounts VALUES (262, 57, '147.96');
INSERT INTO accounts VALUES (280, 57, '187.14');
INSERT INTO accounts VALUES (321, 192, '745.817');
INSERT INTO accounts VALUES (346, 192, '127.9');
INSERT INTO accounts VALUES (414, 57, '25.41');
INSERT INTO accounts VALUES (427, 57, '1168.32');
INSERT INTO accounts VALUES (451, 192, '658.26');

CREATE TABLE documents (
       document_id INTEGER NOT NULL,
       document_type_code VARCHAR(255) NOT NULL,
       project_id INTEGER NOT NULL,
       document_date TIMESTAMP,
       document_name VARCHAR(255),
       document_description VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (document_id)
);

INSERT INTO documents VALUES (29, 'CV', 30, '2004-08-28 06:59:19', 'Review on UK files', NULL, NULL);
INSERT INTO documents VALUES (42, 'BK', 105, '2012-12-27 19:09:18', 'Review on Canadian files', NULL, NULL);
INSERT INTO documents VALUES (57, 'CV', 195, '1980-10-22 14:17:11', 'Review on French files', NULL, NULL);
INSERT INTO documents VALUES (121, 'BK', 105, '1981-11-29 10:23:01', 'Review on USA files', NULL, NULL);
INSERT INTO documents VALUES (181, 'PP', 105, '1970-06-17 14:03:21', 'Chapter on private files', NULL, NULL);
INSERT INTO documents VALUES (192, 'PP', 134, '2013-01-26 15:15:25', 'Book on USA files', NULL, NULL);
INSERT INTO documents VALUES (226, 'BK', 30, '1991-07-08 08:49:59', 'Review on UK files', NULL, NULL);
INSERT INTO documents VALUES (227, 'BK', 30, '1970-03-06 07:34:49', 'Deontae files', NULL, NULL);
INSERT INTO documents VALUES (240, 'BK', 105, '1971-06-09 19:03:41', 'Winona Book', NULL, NULL);
INSERT INTO documents VALUES (300, 'FM', 35, '2007-09-26 02:39:11', 'Trenton Presentation', NULL, NULL);
INSERT INTO documents VALUES (309, 'BK', 35, '1978-10-15 10:33:17', 'Noel CV', NULL, NULL);
INSERT INTO documents VALUES (318, 'PP', 134, '1970-01-30 10:53:35', 'King Book', NULL, NULL);
INSERT INTO documents VALUES (367, 'CV', 134, '1983-08-24 17:10:26', 'Jevon Paper', NULL, NULL);
INSERT INTO documents VALUES (371, 'PP', 105, '1976-05-06 12:56:12', 'Katheryn statement', NULL, NULL);
INSERT INTO documents VALUES (383, 'PP', 35, '2005-10-28 03:17:16', 'Review on UK files', NULL, NULL);

CREATE TABLE documents_with_expenses (
       document_id INTEGER NOT NULL,
       budget_type_code VARCHAR(255) NOT NULL,
       document_details VARCHAR(255),
       primary KEY (document_id)
);

INSERT INTO documents_with_expenses VALUES (57, 'GV', 'government');
INSERT INTO documents_with_expenses VALUES (192, 'GV', 'government');
INSERT INTO documents_with_expenses VALUES (226, 'GV', 'government');
INSERT INTO documents_with_expenses VALUES (227, 'GV', 'government');
INSERT INTO documents_with_expenses VALUES (240, 'GV', 'government');
INSERT INTO documents_with_expenses VALUES (300, 'GV', 'government');
INSERT INTO documents_with_expenses VALUES (309, 'SF', 'safety');
INSERT INTO documents_with_expenses VALUES (367, 'SF', 'safety');
INSERT INTO documents_with_expenses VALUES (371, 'ORG', 'organization');
INSERT INTO documents_with_expenses VALUES (383, 'ORG', 'organization');

CREATE TABLE projects (
       project_id INTEGER NOT NULL,
       project_details VARCHAR(255),
       primary KEY (project_id)
);

INSERT INTO projects VALUES (30, 'Society Research project');
INSERT INTO projects VALUES (35, 'Internet of Things project');
INSERT INTO projects VALUES (105, 'Graph Database project');
INSERT INTO projects VALUES (134, 'Human Resource project');
INSERT INTO projects VALUES (195, 'Population Research project');

CREATE TABLE ref_budget_codes (
       budget_type_code VARCHAR(255) NOT NULL,
       budget_type_description VARCHAR(255) NOT NULL,
       primary KEY (budget_type_code)
);

INSERT INTO ref_budget_codes VALUES ('GV', 'Government');
INSERT INTO ref_budget_codes VALUES ('ORG', 'Organisation');
INSERT INTO ref_budget_codes VALUES ('SF', 'Self founded');

CREATE TABLE ref_document_types (
       document_type_code VARCHAR(255) NOT NULL,
       document_type_name VARCHAR(255) NOT NULL,
       document_type_description VARCHAR(255) NOT NULL,
       primary KEY (document_type_code)
);

INSERT INTO ref_document_types VALUES ('BK', 'Book', 'excellent');
INSERT INTO ref_document_types VALUES ('CV', 'CV', 'excellent');
INSERT INTO ref_document_types VALUES ('PT', 'Presentation', 'very good');
INSERT INTO ref_document_types VALUES ('PP', 'Paper', 'good');
INSERT INTO ref_document_types VALUES ('FM', 'Film', 'fun');

CREATE TABLE statements (
       statement_id INTEGER NOT NULL,
       statement_details VARCHAR(255),
       primary KEY (statement_id)
);

INSERT INTO statements VALUES (57, 'Open Project');
INSERT INTO statements VALUES (192, 'Private Project');

COMMIT;