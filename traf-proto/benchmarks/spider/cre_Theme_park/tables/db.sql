BEGIN;

CREATE TABLE features (
       feature_id INTEGER NOT NULL,
       feature_details VARCHAR(255),
       primary KEY (feature_id)
);

INSERT INTO features VALUES (523, 'cafe');
INSERT INTO features VALUES (528, 'park');
INSERT INTO features VALUES (543, 'garden');
INSERT INTO features VALUES (681, 'shopping');
INSERT INTO features VALUES (955, 'parking');

CREATE TABLE hotels (
       hotel_id INTEGER NOT NULL,
       star_rating_code VARCHAR(255) NOT NULL,
       pets_allowed_yn VARCHAR(255),
       price_range real,
       other_hotel_details VARCHAR(255),
       primary KEY (hotel_id)
);

INSERT INTO hotels VALUES (123, '5', '1', 2914989.571, NULL);
INSERT INTO hotels VALUES (144, '4', '', NULL, NULL);
INSERT INTO hotels VALUES (172, '5', '', 17012.682586009, NULL);
INSERT INTO hotels VALUES (222, '5', '1', NULL, NULL);
INSERT INTO hotels VALUES (239, '3', '1', NULL, NULL);
INSERT INTO hotels VALUES (264, '1', '1', 48525.4530675, NULL);
INSERT INTO hotels VALUES (314, '5', '1', 766712918.96763, NULL);
INSERT INTO hotels VALUES (331, '1', '1', NULL, NULL);
INSERT INTO hotels VALUES (350, '1', '', NULL, NULL);
INSERT INTO hotels VALUES (373, '5', '1', 250548014.90329, NULL);
INSERT INTO hotels VALUES (376, '2', '', NULL, NULL);
INSERT INTO hotels VALUES (379, '4', '1', 38014975.47848, NULL);
INSERT INTO hotels VALUES (420, '5', '1', 9393.86291219, NULL);
INSERT INTO hotels VALUES (421, '3', '', 5526556.6412, NULL);
INSERT INTO hotels VALUES (426, '5', '', 245.067720121, NULL);
INSERT INTO hotels VALUES (431, '2', '1', 43.729525, NULL);
INSERT INTO hotels VALUES (442, '2', '1', 289775.7331715, NULL);
INSERT INTO hotels VALUES (473, '1', '1', 2374.7971074, NULL);
INSERT INTO hotels VALUES (514, '5', '', 1381255.81865, NULL);
INSERT INTO hotels VALUES (555, '5', '1', 5390.432113, NULL);

CREATE TABLE locations (
       location_id INTEGER NOT NULL,
       location_name VARCHAR(255),
       address VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (location_id)
);

INSERT INTO locations VALUES (333, 'Astro Orbiter', '660 Shea Crescent', NULL);
INSERT INTO locations VALUES (368, 'African Animals', '254 Ottilie Junction', NULL);
INSERT INTO locations VALUES (417, 'American Adventure', '53815 Sawayn Tunnel Apt. 297', NULL);
INSERT INTO locations VALUES (579, 'The Barnstormer', '3374 Sarina Manor', NULL);
INSERT INTO locations VALUES (603, 'African Adventure', '88271 Barrows Union Suite 203', NULL);
INSERT INTO locations VALUES (650, 'UK Gallery', '4411 Sabrina Radial Suite 582', NULL);
INSERT INTO locations VALUES (655, 'The Boneyard', '0692 Georgiana Pass', NULL);
INSERT INTO locations VALUES (661, 'Shark World', '2485 Mueller Squares Suite 537', NULL);
INSERT INTO locations VALUES (740, 'Space Spin', '5536 Betsy Street Apt. 646', NULL);
INSERT INTO locations VALUES (759, 'Butterflies', '959 Feest Glen Suite 523', NULL);
INSERT INTO locations VALUES (858, 'Soak Station', '4908 Reinger Vista', NULL);
INSERT INTO locations VALUES (861, 'Castle', '14034 Kohler Drive', NULL);
INSERT INTO locations VALUES (867, 'Coral Reefs', '4510 Schuster Stream Apt. 613', NULL);
INSERT INTO locations VALUES (868, 'Film Festival', '770 Edd Lane Apt. 098', NULL);
INSERT INTO locations VALUES (885, 'Fossil Fun Games', '101 Paucek Crescent', NULL);

CREATE TABLE museums (
       museum_id INTEGER NOT NULL,
       museum_details VARCHAR(255),
       primary KEY (museum_id)
);

INSERT INTO museums VALUES (2113, 'Yale Center for British Art');
INSERT INTO museums VALUES (2701, 'The Metropolitan Museum of Art');
INSERT INTO museums VALUES (5076, 'MoMA');

CREATE TABLE photos (
       photo_id INTEGER NOT NULL,
       tourist_attraction_id INTEGER NOT NULL,
       name VARCHAR(255),
       description VARCHAR(255),
       filename VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (photo_id)
);

INSERT INTO photos VALUES (211, 8449, 'game1', NULL, '702', NULL);
INSERT INTO photos VALUES (280, 7067, 'game2', NULL, '762', NULL);
INSERT INTO photos VALUES (303, 5076, 'game3', NULL, '392', NULL);
INSERT INTO photos VALUES (327, 9919, 'fun1', NULL, '820', NULL);
INSERT INTO photos VALUES (332, 5076, 'fun2', NULL, '060', NULL);
INSERT INTO photos VALUES (428, 6523, 'fun3', NULL, '148', NULL);
INSERT INTO photos VALUES (435, 8429, 'fun4', NULL, '453', NULL);
INSERT INTO photos VALUES (437, 2701, 'fun5', NULL, '128', NULL);
INSERT INTO photos VALUES (525, 5265, 'park1', NULL, '538', NULL);
INSERT INTO photos VALUES (534, 6852, 'park2', NULL, '325', NULL);
INSERT INTO photos VALUES (537, 6653, 'park3', NULL, '695', NULL);
INSERT INTO photos VALUES (550, 5076, 'din1', NULL, '259', NULL);
INSERT INTO photos VALUES (558, 8698, 'din2', NULL, '863', NULL);
INSERT INTO photos VALUES (571, 6653, 'din3', NULL, '864', NULL);
INSERT INTO photos VALUES (596, 9561, 'din4', NULL, '141', NULL);

CREATE TABLE ref_attraction_types (
       attraction_type_code VARCHAR(255) NOT NULL,
       attraction_type_description VARCHAR(255),
       primary KEY (attraction_type_code),
       unique (Attraction_Type_Code)
);

INSERT INTO ref_attraction_types VALUES ('2', 'park');
INSERT INTO ref_attraction_types VALUES ('3', 'garden');
INSERT INTO ref_attraction_types VALUES ('5', 'gallery');
INSERT INTO ref_attraction_types VALUES ('6', 'adventure');
INSERT INTO ref_attraction_types VALUES ('9', 'museum');

CREATE TABLE ref_hotel_star_ratings (
       star_rating_code VARCHAR(255) NOT NULL,
       star_rating_description VARCHAR(255),
       primary KEY (star_rating_code),
       unique (star_rating_code)
);

INSERT INTO ref_hotel_star_ratings VALUES ('1', 'star');
INSERT INTO ref_hotel_star_ratings VALUES ('2', 'star');
INSERT INTO ref_hotel_star_ratings VALUES ('3', 'star');
INSERT INTO ref_hotel_star_ratings VALUES ('4', 'star');
INSERT INTO ref_hotel_star_ratings VALUES ('5', 'star');

CREATE TABLE royal_family (
       royal_family_id INTEGER NOT NULL,
       royal_family_details VARCHAR(255),
       primary KEY (royal_family_id)
);

INSERT INTO royal_family VALUES (9561, NULL);
INSERT INTO royal_family VALUES (9919, NULL);

CREATE TABLE shops (
       shop_id INTEGER NOT NULL,
       shop_details VARCHAR(255),
       primary KEY (shop_id)
);

INSERT INTO shops VALUES (8429, 'soup');
INSERT INTO shops VALUES (8449, 'coffee');
INSERT INTO shops VALUES (8698, 'Flower');
INSERT INTO shops VALUES (9360, 'see food');

CREATE TABLE staff (
       staff_id INTEGER NOT NULL,
       tourist_attraction_id INTEGER NOT NULL,
       name VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (staff_id)
);

INSERT INTO staff VALUES (170, 6476, 'Whitney', NULL);
INSERT INTO staff VALUES (219, 6476, 'Kaela', NULL);
INSERT INTO staff VALUES (237, 7067, 'Eunice', NULL);
INSERT INTO staff VALUES (249, 5265, 'Kiarra', NULL);
INSERT INTO staff VALUES (310, 9561, 'Phoebe', NULL);
INSERT INTO staff VALUES (433, 9360, 'Vickie', NULL);
INSERT INTO staff VALUES (463, 6653, 'Jannie', NULL);
INSERT INTO staff VALUES (470, 6523, 'Lenore', NULL);
INSERT INTO staff VALUES (487, 6852, 'Asia', NULL);
INSERT INTO staff VALUES (491, 6852, 'Janet', NULL);
INSERT INTO staff VALUES (532, 6852, 'Elouise', NULL);
INSERT INTO staff VALUES (591, 9360, 'Gina', NULL);
INSERT INTO staff VALUES (595, 8698, 'Beth', NULL);
INSERT INTO staff VALUES (596, 2701, 'Ruthie', NULL);
INSERT INTO staff VALUES (604, 6852, 'Aurore', NULL);
INSERT INTO staff VALUES (619, 2113, 'Cortney', NULL);
INSERT INTO staff VALUES (643, 6523, 'Astrid', NULL);
INSERT INTO staff VALUES (667, 9561, 'Shemar', NULL);
INSERT INTO staff VALUES (860, 6476, 'Trinity', NULL);
INSERT INTO staff VALUES (952, 5265, 'Carmella', NULL);

CREATE TABLE street_markets (
       market_id INTEGER NOT NULL,
       market_details VARCHAR(255),
       primary KEY (market_id)
);

INSERT INTO street_markets VALUES (6852, 'Broadway');
INSERT INTO street_markets VALUES (7067, 'Fish Farm Market');

CREATE TABLE theme_parks (
       theme_park_id INTEGER NOT NULL,
       theme_park_details VARCHAR(255),
       primary KEY (theme_park_id)
);

INSERT INTO theme_parks VALUES (5265, 'Disney');
INSERT INTO theme_parks VALUES (6476, 'Sea World');
INSERT INTO theme_parks VALUES (6523, 'Universal Studios');

CREATE TABLE tourist_attraction_features (
       tourist_attraction_id INTEGER NOT NULL,
       feature_id INTEGER NOT NULL,
       primary KEY (tourist_attraction_id, feature_id)
);

INSERT INTO tourist_attraction_features VALUES (5076, 528);
INSERT INTO tourist_attraction_features VALUES (5076, 681);
INSERT INTO tourist_attraction_features VALUES (5265, 523);
INSERT INTO tourist_attraction_features VALUES (5265, 955);
INSERT INTO tourist_attraction_features VALUES (6476, 543);
INSERT INTO tourist_attraction_features VALUES (6476, 681);
INSERT INTO tourist_attraction_features VALUES (6476, 955);
INSERT INTO tourist_attraction_features VALUES (6523, 528);
INSERT INTO tourist_attraction_features VALUES (6852, 528);
INSERT INTO tourist_attraction_features VALUES (6852, 955);
INSERT INTO tourist_attraction_features VALUES (7067, 543);
INSERT INTO tourist_attraction_features VALUES (8429, 681);
INSERT INTO tourist_attraction_features VALUES (8449, 528);
INSERT INTO tourist_attraction_features VALUES (8698, 528);
INSERT INTO tourist_attraction_features VALUES (8698, 543);
INSERT INTO tourist_attraction_features VALUES (8698, 681);
INSERT INTO tourist_attraction_features VALUES (9561, 681);
INSERT INTO tourist_attraction_features VALUES (9919, 681);

CREATE TABLE tourist_attractions (
       tourist_attraction_id INTEGER NOT NULL,
       attraction_type_code VARCHAR(255) NOT NULL,
       location_id INTEGER NOT NULL,
       how_to_get_there VARCHAR(255),
       name VARCHAR(255),
       description VARCHAR(255),
       opening_hours VARCHAR(255),
       other_details VARCHAR(255),
       primary KEY (tourist_attraction_id)
);

INSERT INTO tourist_attractions VALUES (2113, '2', 579, 'bus', 'art museum', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (2701, '6', 417, 'walk', 'UK gallery', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (5076, '2', 868, 'shuttle', 'flying elephant', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (5265, '5', 603, 'bus', 'film festival', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (6476, '3', 417, 'shuttle', 'US museum', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (6523, '9', 858, 'walk', 'fun games', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (6653, '9', 655, 'walk', 'history gallery', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (6852, '5', 858, 'walk', 'exploration trial', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (7067, '5', 417, 'bus', 'haunted mansion', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (8429, '9', 867, 'walk', 'presidents hall', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (8449, '2', 579, 'bus', 'impressions de France', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (8698, '5', 661, 'bus', 'jungle cruise', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (9360, '5', 868, 'shuttle', 'fun shops', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (9561, '2', 759, 'bus', 'cafe', NULL, NULL, NULL);
INSERT INTO tourist_attractions VALUES (9919, '6', 579, 'shuttle', 'parking', NULL, NULL, NULL);

CREATE TABLE visitors (
       tourist_id INTEGER NOT NULL,
       tourist_details VARCHAR(255),
       primary KEY (tourist_id),
       unique (Tourist_ID)
);

INSERT INTO visitors VALUES (164, 'Toney');
INSERT INTO visitors VALUES (189, 'Graciela');
INSERT INTO visitors VALUES (204, 'Vincent');
INSERT INTO visitors VALUES (211, 'Vivian');
INSERT INTO visitors VALUES (241, 'Nettie');
INSERT INTO visitors VALUES (295, 'Laurence');
INSERT INTO visitors VALUES (359, 'Newell');
INSERT INTO visitors VALUES (377, 'Marisol');
INSERT INTO visitors VALUES (399, 'Jarrell');
INSERT INTO visitors VALUES (439, 'Edna');
INSERT INTO visitors VALUES (500, 'Maud');
INSERT INTO visitors VALUES (513, 'Alison');
INSERT INTO visitors VALUES (541, 'Rosalind');
INSERT INTO visitors VALUES (545, 'Tevin');
INSERT INTO visitors VALUES (578, 'Aleen');
INSERT INTO visitors VALUES (610, 'Marcelle');
INSERT INTO visitors VALUES (652, 'Lizzie');
INSERT INTO visitors VALUES (779, 'Wayne');
INSERT INTO visitors VALUES (841, 'Teresa');
INSERT INTO visitors VALUES (888, 'Elnora');

CREATE TABLE visits (
       visit_id INTEGER NOT NULL,
       tourist_attraction_id INTEGER NOT NULL,
       tourist_id INTEGER NOT NULL,
       visit_date DATETIME NOT NULL,
       visit_details VARCHAR(255) NOT NULL,
       primary KEY (visit_id)
);

INSERT INTO visits VALUES (183, 6653, 377, '2004-08-21 03:06:14', '');
INSERT INTO visits VALUES (268, 5076, 204, '2013-08-06 05:35:51', '');
INSERT INTO visits VALUES (273, 9360, 211, '2013-10-27 09:56:08', '');
INSERT INTO visits VALUES (302, 6476, 377, '1990-08-15 14:24:10', '');
INSERT INTO visits VALUES (356, 6476, 439, '1980-11-26 02:08:00', '');
INSERT INTO visits VALUES (381, 6523, 211, '2017-03-19 08:48:19', '');
INSERT INTO visits VALUES (416, 6476, 841, '2008-11-09 01:28:01', '');
INSERT INTO visits VALUES (479, 6852, 439, '1989-08-24 20:26:37', '');
INSERT INTO visits VALUES (563, 6852, 610, '1993-02-01 15:27:20', '');
INSERT INTO visits VALUES (612, 9919, 204, '2007-09-17 10:12:45', '');
INSERT INTO visits VALUES (729, 6476, 513, '1998-05-12 00:50:20', '');
INSERT INTO visits VALUES (776, 8698, 513, '2010-10-04 01:34:12', '');
INSERT INTO visits VALUES (781, 6852, 779, '2018-01-09 20:39:52', '');
INSERT INTO visits VALUES (866, 8429, 545, '1971-12-16 06:41:26', '');
INSERT INTO visits VALUES (909, 8698, 779, '1998-12-10 02:46:43', '');
INSERT INTO visits VALUES (937, 6523, 541, '1996-01-08 13:23:41', '');
INSERT INTO visits VALUES (962, 9919, 610, '2007-09-03 04:30:01', '');
INSERT INTO visits VALUES (968, 6852, 377, '1974-12-31 23:18:24', '');
INSERT INTO visits VALUES (977, 8698, 500, '2001-11-13 10:08:28', '');
INSERT INTO visits VALUES (999, 2701, 610, '1990-11-12 00:54:50', '');

COMMIT;