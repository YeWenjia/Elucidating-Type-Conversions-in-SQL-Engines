BEGIN;

CREATE TABLE addresses (
       address_id INTEGER NOT NULL,
       address_details VARCHAR(255),
       primary KEY (address_id),
       unique (Address_ID)
);

INSERT INTO addresses VALUES (1, '465 Emely Bypass
West Mafalda, CO 23309');
INSERT INTO addresses VALUES (2, '669 Carter Trafficway
Port Delbert, OK 66249');
INSERT INTO addresses VALUES (3, '38247 Ernser Gateway Suite 442
Bogisichland, VT 71460');
INSERT INTO addresses VALUES (4, '732 Greenholt Valleys
East Marionfort, VT 89477-0433');
INSERT INTO addresses VALUES (5, '382 Demond Alley
Luellamouth, MT 67912');
INSERT INTO addresses VALUES (6, '3851 Quigley Flats
O''Reillychester, CA 92522-9526');
INSERT INTO addresses VALUES (7, '78950 Kamryn Centers
Chelsealand, NE 22947-6129');
INSERT INTO addresses VALUES (8, '682 Kautzer Forest Apt. 509
Jaydenfurt, NE 85011-5059');
INSERT INTO addresses VALUES (9, '11093 Balistreri Forge
Gaylordtown, VT 05705');
INSERT INTO addresses VALUES (10, '9113 Wisoky Glen Apt. 601
Lake Immanuel, UT 01388');
INSERT INTO addresses VALUES (11, '73409 Linnea Loop Apt. 778
Haagberg, AK 41204-1496');
INSERT INTO addresses VALUES (12, '8220 Concepcion Neck Suite 394
East Beauview, LA 19968-4755');
INSERT INTO addresses VALUES (13, '513 Lindgren River
North Scottymouth, IN 85224-1392');
INSERT INTO addresses VALUES (14, '9694 Wava Roads
Ricechester, DC 70816-9058');
INSERT INTO addresses VALUES (15, '068 O''Connell Tunnel
West Colemanburgh, MO 87777');

CREATE TABLE agreements (
       document_id INTEGER NOT NULL,
       event_id INTEGER NOT NULL,
       primary KEY (document_id)
);

INSERT INTO agreements VALUES (1, 13);
INSERT INTO agreements VALUES (2, 13);
INSERT INTO agreements VALUES (3, 15);
INSERT INTO agreements VALUES (4, 9);
INSERT INTO agreements VALUES (5, 11);
INSERT INTO agreements VALUES (6, 8);
INSERT INTO agreements VALUES (7, 10);
INSERT INTO agreements VALUES (8, 15);
INSERT INTO agreements VALUES (9, 6);
INSERT INTO agreements VALUES (10, 11);
INSERT INTO agreements VALUES (11, 8);
INSERT INTO agreements VALUES (12, 9);
INSERT INTO agreements VALUES (13, 5);
INSERT INTO agreements VALUES (14, 12);
INSERT INTO agreements VALUES (15, 15);

CREATE TABLE assets (
       asset_id INTEGER NOT NULL,
       other_details VARCHAR(255),
       primary KEY (asset_id)
);

INSERT INTO assets VALUES (1, 'Transportation Cars');
INSERT INTO assets VALUES (2, 'Meeting Rooms');
INSERT INTO assets VALUES (3, 'Dinning Tables');

CREATE TABLE assets_in_events (
       asset_id INTEGER NOT NULL,
       event_id INTEGER NOT NULL,
       primary KEY (asset_id, event_id)
);

INSERT INTO assets_in_events VALUES (1, 4);
INSERT INTO assets_in_events VALUES (1, 5);
INSERT INTO assets_in_events VALUES (1, 9);
INSERT INTO assets_in_events VALUES (1, 10);
INSERT INTO assets_in_events VALUES (2, 8);
INSERT INTO assets_in_events VALUES (2, 14);
INSERT INTO assets_in_events VALUES (3, 2);
INSERT INTO assets_in_events VALUES (3, 5);
INSERT INTO assets_in_events VALUES (3, 8);
INSERT INTO assets_in_events VALUES (3, 9);
INSERT INTO assets_in_events VALUES (3, 10);
INSERT INTO assets_in_events VALUES (3, 12);

CREATE TABLE channels (
       channel_id INTEGER NOT NULL,
       other_details VARCHAR(255),
       primary KEY (channel_id)
);

INSERT INTO channels VALUES (1, '145');
INSERT INTO channels VALUES (2, '348');
INSERT INTO channels VALUES (3, '933');
INSERT INTO channels VALUES (4, '631');
INSERT INTO channels VALUES (5, '681');
INSERT INTO channels VALUES (6, '993');
INSERT INTO channels VALUES (7, '249');
INSERT INTO channels VALUES (8, '644');
INSERT INTO channels VALUES (9, '668');
INSERT INTO channels VALUES (10, '058');
INSERT INTO channels VALUES (11, '163');
INSERT INTO channels VALUES (12, '285');
INSERT INTO channels VALUES (13, '943');
INSERT INTO channels VALUES (14, '292');
INSERT INTO channels VALUES (15, '177');

CREATE TABLE events (
       event_id INTEGER NOT NULL,
       address_id INTEGER,
       channel_id INTEGER NOT NULL,
       event_type_code VARCHAR(255),
       finance_id INTEGER NOT NULL,
       location_id INTEGER NOT NULL,
       primary KEY (event_id),
       unique (Event_ID)
);

INSERT INTO events VALUES (1, 3, 12, 'Trade Show', 2, 13);
INSERT INTO events VALUES (2, 15, 13, 'Press Conferenc', 8, 11);
INSERT INTO events VALUES (3, 12, 1, 'Press Conferenc', 12, 6);
INSERT INTO events VALUES (4, 13, 10, 'Ceremonies', 7, 6);
INSERT INTO events VALUES (5, 9, 4, 'Trade Show', 15, 6);
INSERT INTO events VALUES (6, 15, 12, 'Seminar', 15, 9);
INSERT INTO events VALUES (7, 15, 6, 'Trade Show', 13, 15);
INSERT INTO events VALUES (8, 3, 15, 'Trade Show', 1, 6);
INSERT INTO events VALUES (9, 12, 3, 'Press Conferenc', 3, 11);
INSERT INTO events VALUES (10, 15, 10, 'Conference', 7, 12);
INSERT INTO events VALUES (11, 10, 4, 'Trade Show', 2, 8);
INSERT INTO events VALUES (12, 14, 9, 'Trade Show', 14, 7);
INSERT INTO events VALUES (13, 12, 13, 'Trade Show', 12, 12);
INSERT INTO events VALUES (14, 10, 11, 'Seminar', 5, 10);
INSERT INTO events VALUES (15, 2, 2, 'Conference', 10, 5);

CREATE TABLE finances (
       finance_id INTEGER NOT NULL,
       other_details VARCHAR(255),
       primary KEY (finance_id)
);

INSERT INTO finances VALUES (1, 'Mutual');
INSERT INTO finances VALUES (2, 'Good');
INSERT INTO finances VALUES (3, 'Bad');
INSERT INTO finances VALUES (4, 'Mutual');
INSERT INTO finances VALUES (5, 'Bad');
INSERT INTO finances VALUES (6, 'Good');
INSERT INTO finances VALUES (7, 'Good');
INSERT INTO finances VALUES (8, 'Mutual');
INSERT INTO finances VALUES (9, 'Bad');
INSERT INTO finances VALUES (10, 'Bad');
INSERT INTO finances VALUES (11, 'Mutual');
INSERT INTO finances VALUES (12, 'Mutual');
INSERT INTO finances VALUES (13, 'Good');
INSERT INTO finances VALUES (14, 'Good');
INSERT INTO finances VALUES (15, 'Mutual');

CREATE TABLE locations (
       location_id INTEGER NOT NULL,
       other_details VARCHAR(255),
       primary KEY (location_id)
);

INSERT INTO locations VALUES (1, 'Rowe PLC');
INSERT INTO locations VALUES (2, 'Ebert, Green and Bogisich');
INSERT INTO locations VALUES (3, 'Prohaska LLC');
INSERT INTO locations VALUES (4, 'White, Kassulke and Barrows');
INSERT INTO locations VALUES (5, 'Wintheiser-Sauer');
INSERT INTO locations VALUES (6, 'Morar-Denesik');
INSERT INTO locations VALUES (7, 'Rowe-Stoltenberg');
INSERT INTO locations VALUES (8, 'Price-Lynch');
INSERT INTO locations VALUES (9, 'Ryan-Wyman');
INSERT INTO locations VALUES (10, 'Hilll Ltd');
INSERT INTO locations VALUES (11, 'Fritsch LLC');
INSERT INTO locations VALUES (12, 'Kuvalis-Goodwin');
INSERT INTO locations VALUES (13, 'Sanford Inc');
INSERT INTO locations VALUES (14, 'Waelchi-Wehner');
INSERT INTO locations VALUES (15, 'Daugherty, Nader and Balistreri');

CREATE TABLE parties (
       party_id INTEGER NOT NULL,
       party_details VARCHAR(255),
       primary KEY (party_id)
);

INSERT INTO parties VALUES (3, 'European People''s Party');
INSERT INTO parties VALUES (4, 'European Free Alliance');
INSERT INTO parties VALUES (5, 'European Alliance for Freedom');
INSERT INTO parties VALUES (6, 'European Christian Political Movement');
INSERT INTO parties VALUES (7, 'Movement for a Europe of Nations and Freedom');
INSERT INTO parties VALUES (8, 'Alliance of Liberals and Democrats for Europe');
INSERT INTO parties VALUES (9, 'EUDemocrats');

CREATE TABLE parties_in_events (
       party_id INTEGER NOT NULL,
       event_id INTEGER NOT NULL,
       role_code VARCHAR(255),
       primary KEY (party_id, event_id)
);

INSERT INTO parties_in_events VALUES (3, 7, 'Organizer');
INSERT INTO parties_in_events VALUES (3, 8, 'Participant');
INSERT INTO parties_in_events VALUES (4, 1, 'Organizer');
INSERT INTO parties_in_events VALUES (4, 3, 'Participant');
INSERT INTO parties_in_events VALUES (4, 8, 'Organizer');
INSERT INTO parties_in_events VALUES (5, 9, 'Participant');
INSERT INTO parties_in_events VALUES (5, 10, 'Participant');
INSERT INTO parties_in_events VALUES (5, 15, 'Organizer');
INSERT INTO parties_in_events VALUES (6, 6, 'Organizer');
INSERT INTO parties_in_events VALUES (6, 12, 'Participant');
INSERT INTO parties_in_events VALUES (6, 13, 'Organizer');
INSERT INTO parties_in_events VALUES (9, 3, 'Participant');
INSERT INTO parties_in_events VALUES (9, 4, 'Participant');
INSERT INTO parties_in_events VALUES (9, 10, 'Organizer');
INSERT INTO parties_in_events VALUES (9, 12, 'Organizer');

CREATE TABLE products (
       product_id INTEGER NOT NULL,
       product_type_code VARCHAR(255),
       product_name VARCHAR(255),
       product_price DECIMAL(20,4),
       primary KEY (product_id),
       unique (Product_ID)
);

INSERT INTO products VALUES (1, 'Books', 'Business Policy', 1336.26);
INSERT INTO products VALUES (3, 'Food', 'Special Dinning', 2894.94);
INSERT INTO products VALUES (5, 'Clothes', 'Men suits', 3298.84);
INSERT INTO products VALUES (6, 'Electronics', 'TV Equipments', 932.25);
INSERT INTO products VALUES (7, 'Books', 'Business Policy B', 3215.66);
INSERT INTO products VALUES (10, 'Electronics', 'TV Equipments', 4427.49);
INSERT INTO products VALUES (11, 'Electronics', 'Conference Equipments', 3289.47);
INSERT INTO products VALUES (18, 'Books', 'Trading Policy', 3228.49);
INSERT INTO products VALUES (20, 'Books', 'Trading Policy B', 4343.83);
INSERT INTO products VALUES (22, 'Food', 'Dinning', 3574.56);
INSERT INTO products VALUES (24, 'Food', 'Dinning', 4895.86);
INSERT INTO products VALUES (26, 'Food', 'Dinning', 2339.97);
INSERT INTO products VALUES (29, 'Food', 'Special Dinning', 502.15);
INSERT INTO products VALUES (34, 'Electronics', 'TV Equipments', 970.77);
INSERT INTO products VALUES (45, 'Clothes', 'Men suits', 3541.17);

CREATE TABLE products_in_events (
       product_in_event_id INTEGER NOT NULL,
       event_id INTEGER NOT NULL,
       product_id INTEGER NOT NULL,
       primary KEY (product_in_event_id)
);

INSERT INTO products_in_events VALUES (13, 4, 29);
INSERT INTO products_in_events VALUES (23, 8, 3);
INSERT INTO products_in_events VALUES (32, 14, 10);
INSERT INTO products_in_events VALUES (33, 5, 18);
INSERT INTO products_in_events VALUES (43, 4, 45);
INSERT INTO products_in_events VALUES (46, 7, 3);
INSERT INTO products_in_events VALUES (50, 14, 6);
INSERT INTO products_in_events VALUES (61, 7, 3);
INSERT INTO products_in_events VALUES (63, 6, 34);
INSERT INTO products_in_events VALUES (64, 15, 6);
INSERT INTO products_in_events VALUES (69, 8, 20);
INSERT INTO products_in_events VALUES (74, 1, 6);
INSERT INTO products_in_events VALUES (79, 4, 45);
INSERT INTO products_in_events VALUES (90, 14, 26);
INSERT INTO products_in_events VALUES (99, 10, 11);

COMMIT;