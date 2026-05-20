BEGIN;

CREATE TABLE all_documents (
       document_id INTEGER NOT NULL,
       date_stored TIMESTAMP,
       document_type_code VARCHAR(255) NOT NULL,
       document_name VARCHAR(255),
       document_description VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (document_id)
);

INSERT INTO all_documents VALUES (7, '1976-06-15 03:40:06', 'CV', 'Robin CV', NULL, NULL);
INSERT INTO all_documents VALUES (11, '1986-10-14 17:53:39', 'CV', 'Marry CV', NULL, NULL);
INSERT INTO all_documents VALUES (25, '2008-06-08 12:45:38', 'BK', 'One hundred years of solitude', NULL, NULL);
INSERT INTO all_documents VALUES (39, '2012-07-03 09:48:46', 'BK', 'How to read a book', NULL, NULL);
INSERT INTO all_documents VALUES (72, '2012-07-03 09:48:46', 'CV', 'Alan CV', NULL, NULL);
INSERT INTO all_documents VALUES (81, '1995-01-01 03:52:11', 'BK', 'Hua Mulan', NULL, NULL);
INSERT INTO all_documents VALUES (99, '2008-06-08 12:45:38', 'CV', 'Leon CV', NULL, NULL);
INSERT INTO all_documents VALUES (111, '1987-11-05 06:11:22', 'PR', 'Learning features of CNN', NULL, NULL);
INSERT INTO all_documents VALUES (119, '2008-06-08 12:45:38', 'RV', 'Marriage and population', NULL, NULL);
INSERT INTO all_documents VALUES (120, '1997-03-10 15:24:00', 'RV', 'Society and tax', NULL, NULL);
INSERT INTO all_documents VALUES (166, '1997-03-10 15:24:00', 'PR', 'Are you talking to a machine', NULL, NULL);
INSERT INTO all_documents VALUES (170, '2009-08-18 03:29:08', 'RV', 'Population', NULL, NULL);
INSERT INTO all_documents VALUES (230, '1976-06-15 03:40:06', 'CV', 'Martin CV', NULL, NULL);
INSERT INTO all_documents VALUES (252, '1976-06-15 03:40:06', 'BK', 'Summer', NULL, NULL);
INSERT INTO all_documents VALUES (260, '1997-03-10 15:24:00', 'BK', 'Cats and me', NULL, NULL);

CREATE TABLE document_locations (
       document_id INTEGER NOT NULL,
       location_code VARCHAR(255) NOT NULL,
       date_in_location_from DATETIME NOT NULL,
       date_in_locaton_to TIMESTAMP,
       primary KEY (document_id, location_code, date_in_location_from)
);

INSERT INTO document_locations VALUES (7, 'e', '2017-01-06 23:17:22', '2008-06-08 12:45:38');
INSERT INTO document_locations VALUES (11, 'x', '2017-01-06 23:17:22', '2012-07-03 09:48:46');
INSERT INTO document_locations VALUES (81, 'c', '1972-03-31 09:47:22', '1987-11-05 06:11:22');
INSERT INTO document_locations VALUES (81, 'c', '2017-01-06 23:17:22', '2010-11-26 19:22:50');
INSERT INTO document_locations VALUES (81, 'x', '2008-06-08 12:45:38', '1976-06-15 03:40:06');
INSERT INTO document_locations VALUES (111, 'x', '1986-10-14 17:53:39', '2010-11-26 19:22:50');
INSERT INTO document_locations VALUES (119, 'b', '2017-01-06 23:17:22', '1995-01-01 03:52:11');
INSERT INTO document_locations VALUES (166, 'b', '1985-05-13 12:19:43', '1986-10-14 17:53:39');
INSERT INTO document_locations VALUES (166, 'b', '1986-10-14 17:53:39', '2010-11-26 19:22:50');
INSERT INTO document_locations VALUES (170, 'x', '1997-03-10 15:24:00', '1976-06-15 03:40:06');
INSERT INTO document_locations VALUES (230, 'e', '1972-03-31 09:47:22', '1987-11-05 06:11:22');
INSERT INTO document_locations VALUES (230, 'e', '2010-11-26 19:22:50', '2017-01-06 23:17:22');
INSERT INTO document_locations VALUES (252, 'n', '2017-01-06 23:17:22', '1997-03-10 15:24:00');
INSERT INTO document_locations VALUES (252, 'x', '1972-03-31 09:47:22', '2009-08-18 03:29:08');
INSERT INTO document_locations VALUES (260, 'e', '2009-08-18 03:29:08', '1986-10-14 17:53:39');

CREATE TABLE documents_to_be_destroyed (
       document_id INTEGER NOT NULL,
       destruction_authorised_by_employee_id INTEGER,
       destroyed_by_employee_id INTEGER,
       planned_destruction_date TIMESTAMP,
       actual_destruction_date TIMESTAMP,
       other_details VARCHAR(255),
       primary KEY (document_id)
);

INSERT INTO documents_to_be_destroyed VALUES (7, 156, 138, '1988-02-01 14:41:52', '2017-01-06 23:17:22', NULL);
INSERT INTO documents_to_be_destroyed VALUES (11, 55, 173, '2010-11-26 19:22:50', '1986-10-14 17:53:39', NULL);
INSERT INTO documents_to_be_destroyed VALUES (25, 183, 156, '2009-08-18 03:29:08', '1995-01-01 03:52:11', NULL);
INSERT INTO documents_to_be_destroyed VALUES (39, 183, 136, '1976-06-15 03:40:06', '2009-08-18 03:29:08', NULL);
INSERT INTO documents_to_be_destroyed VALUES (99, 55, 99, '2017-01-06 23:17:22', '1986-10-14 17:53:39', NULL);
INSERT INTO documents_to_be_destroyed VALUES (111, 38, 173, '1972-03-31 09:47:22', '2009-08-18 03:29:08', NULL);
INSERT INTO documents_to_be_destroyed VALUES (120, 183, 173, '1972-03-31 09:47:22', '1995-01-01 03:52:11', NULL);
INSERT INTO documents_to_be_destroyed VALUES (166, 156, 38, '1987-11-05 06:11:22', '2012-07-03 09:48:46', NULL);
INSERT INTO documents_to_be_destroyed VALUES (170, 123, 136, '2017-01-06 23:17:22', '1988-02-01 14:41:52', NULL);
INSERT INTO documents_to_be_destroyed VALUES (252, 30, 55, '1972-03-31 09:47:22', '1985-05-13 12:19:43', NULL);
INSERT INTO documents_to_be_destroyed VALUES (260, 55, 99, '2017-01-06 23:17:22', '2017-01-06 23:17:22', NULL);

CREATE TABLE employees (
       employee_id INTEGER NOT NULL,
       role_code VARCHAR(255) NOT NULL,
       employee_name VARCHAR(255),
       gender_mfu VARCHAR(255) NOT NULL,
       date_of_birth DATETIME NOT NULL,
       other_details VARCHAR(255),
       primary KEY (employee_id)
);

INSERT INTO employees VALUES (25, 'HR', 'Leo', '', '1973-02-15 17:16:00', NULL);
INSERT INTO employees VALUES (30, 'MG', 'Ebba', '', '1979-09-20 12:50:15', NULL);
INSERT INTO employees VALUES (38, 'ED', 'Stephanie', '1', '2012-03-30 23:02:28', NULL);
INSERT INTO employees VALUES (55, 'ED', 'Harley', '', '1972-02-18 11:53:30', NULL);
INSERT INTO employees VALUES (57, 'ED', 'Armani', '', '1988-12-08 06:13:33', NULL);
INSERT INTO employees VALUES (71, 'ED', 'Gussie', '', '1973-04-04 21:41:22', NULL);
INSERT INTO employees VALUES (99, 'ED', 'Izabella', '1', '1977-07-04 16:25:21', NULL);
INSERT INTO employees VALUES (123, 'PT', 'Hugh', '', '2010-03-15 00:17:13', NULL);
INSERT INTO employees VALUES (136, 'ED', 'Mallie', '', '1980-12-11 20:28:20', NULL);
INSERT INTO employees VALUES (138, 'ED', 'Beatrice', '1', '2013-04-02 23:55:48', NULL);
INSERT INTO employees VALUES (156, 'PR', 'Diego', '', '1998-05-30 12:54:10', NULL);
INSERT INTO employees VALUES (159, 'PR', 'Arno', '', '2010-06-10 20:36:34', NULL);
INSERT INTO employees VALUES (173, 'PR', 'Alene', '1', '1980-10-14 12:23:10', NULL);
INSERT INTO employees VALUES (181, 'PR', 'Ettie', '1', '1988-08-03 00:11:14', NULL);
INSERT INTO employees VALUES (183, 'PR', 'Jeramie', '', '1993-08-21 05:22:10', NULL);

CREATE TABLE ref_calendar (
       calendar_date DATETIME NOT NULL,
       day_number INTEGER,
       primary KEY (calendar_date)
);

INSERT INTO ref_calendar VALUES ('1972-03-31 09:47:22', 5);
INSERT INTO ref_calendar VALUES ('1976-06-15 03:40:06', 7);
INSERT INTO ref_calendar VALUES ('1985-05-13 12:19:43', 7);
INSERT INTO ref_calendar VALUES ('1986-10-14 17:53:39', 1);
INSERT INTO ref_calendar VALUES ('1987-11-05 06:11:22', 3);
INSERT INTO ref_calendar VALUES ('1988-02-01 14:41:52', 8);
INSERT INTO ref_calendar VALUES ('1994-11-15 03:49:54', 9);
INSERT INTO ref_calendar VALUES ('1995-01-01 03:52:11', 1);
INSERT INTO ref_calendar VALUES ('1997-03-10 15:24:00', 7);
INSERT INTO ref_calendar VALUES ('2007-05-28 16:28:48', 2);
INSERT INTO ref_calendar VALUES ('2008-06-08 12:45:38', 3);
INSERT INTO ref_calendar VALUES ('2009-08-18 03:29:08', 8);
INSERT INTO ref_calendar VALUES ('2010-11-26 19:22:50', 7);
INSERT INTO ref_calendar VALUES ('2012-07-03 09:48:46', 7);
INSERT INTO ref_calendar VALUES ('2017-01-06 23:17:22', 8);

CREATE TABLE ref_document_types (
       document_type_code VARCHAR(255) NOT NULL,
       document_type_name VARCHAR(255) NOT NULL,
       document_type_description VARCHAR(255) NOT NULL,
       primary KEY (document_type_code)
);

INSERT INTO ref_document_types VALUES ('CV', 'CV', '');
INSERT INTO ref_document_types VALUES ('BK', 'Book', '');
INSERT INTO ref_document_types VALUES ('PR', 'Paper', '');
INSERT INTO ref_document_types VALUES ('RV', 'Review', '');

CREATE TABLE ref_locations (
       location_code VARCHAR(255) NOT NULL,
       location_name VARCHAR(255) NOT NULL,
       location_description VARCHAR(255) NOT NULL,
       primary KEY (location_code)
);

INSERT INTO ref_locations VALUES ('b', 'Brazil', '');
INSERT INTO ref_locations VALUES ('c', 'Canada', '');
INSERT INTO ref_locations VALUES ('e', 'Edinburgh', '');
INSERT INTO ref_locations VALUES ('n', 'Nanjing', '');
INSERT INTO ref_locations VALUES ('x', 'Xiamen', '');

CREATE TABLE roles (
       role_code VARCHAR(255) NOT NULL,
       role_name VARCHAR(255),
       role_description VARCHAR(255),
       primary KEY (role_code)
);

INSERT INTO roles VALUES ('MG', 'Manager', 'Vero harum corrupti odit ipsa vero et odio. Iste et recusandae temporibus maxime. Magni aspernatur fugit quis explicabo totam esse corrupti.');
INSERT INTO roles VALUES ('ED', 'Editor', 'Itaque dolor ut nemo rerum vitae provident. Vel laborum ipsum velit sint. Et est omnis dignissimos.');
INSERT INTO roles VALUES ('PT', 'Photo', 'Aut modi nihil molestias temporibus sit rerum. Sit neque eaque odio omnis incidunt.');
INSERT INTO roles VALUES ('PR', 'Proof Reader', 'Ut sed quae eaque mollitia qui hic. Natus ea expedita et odio illum fugiat qui natus. Consequatur velit ut dolorem cum ullam esse deserunt dignissimos. Enim non non rem officiis quis.');
INSERT INTO roles VALUES ('HR', 'Human Resource', 'Et totam est quibusdam aspernatur ut. Vitae perferendis eligendi voluptatem molestiae rem ut enim. Ipsum expedita quae earum unde est. Repellendus ut ipsam nihil accusantium sit. Magni accusantium numquam quod et.');

COMMIT;