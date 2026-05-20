BEGIN;

CREATE TABLE document_functional_areas (
       `document_code` VARCHAR(255) NOT NULL,
       `functional_area_code` VARCHAR(255) NOT NULL
);

INSERT INTO document_functional_areas VALUES ('675', '9');
INSERT INTO document_functional_areas VALUES ('930', '1');
INSERT INTO document_functional_areas VALUES ('217', '1');
INSERT INTO document_functional_areas VALUES ('465', '1');
INSERT INTO document_functional_areas VALUES ('958', '1');
INSERT INTO document_functional_areas VALUES ('958', '9');
INSERT INTO document_functional_areas VALUES ('217', '9');
INSERT INTO document_functional_areas VALUES ('961', '9');
INSERT INTO document_functional_areas VALUES ('928', '9');
INSERT INTO document_functional_areas VALUES ('958', '9');
INSERT INTO document_functional_areas VALUES ('349', '1');
INSERT INTO document_functional_areas VALUES ('961', '8');
INSERT INTO document_functional_areas VALUES ('989', '1');
INSERT INTO document_functional_areas VALUES ('706', '8');
INSERT INTO document_functional_areas VALUES ('713', '8');

CREATE TABLE document_sections (
       `section_id` INTEGER PRIMARY KEY,
       `document_code` VARCHAR(255) NOT NULL,
       `section_sequence` INTEGER,
       `section_code` VARCHAR(255),
       `section_title` VARCHAR(255)
);

INSERT INTO document_sections VALUES (12, '714', 6072, '70', 'after');
INSERT INTO document_sections VALUES (15, '217', 4510, '14', 'after');
INSERT INTO document_sections VALUES (19, '675', 7236, '90', 'after');
INSERT INTO document_sections VALUES (21, '675', 9847, '72', 'before');
INSERT INTO document_sections VALUES (23, '465', 8548, '49', 'after');
INSERT INTO document_sections VALUES (27, '566', 6016, '18', 'before');
INSERT INTO document_sections VALUES (38, '930', 6521, '58', 'after');
INSERT INTO document_sections VALUES (40, '465', 4964, '93', 'after');
INSERT INTO document_sections VALUES (54, '961', 4794, '34', 'before');
INSERT INTO document_sections VALUES (57, '989', 6349, '22', 'after');
INSERT INTO document_sections VALUES (62, '621', 5552, '16', 'after');
INSERT INTO document_sections VALUES (86, '706', 2170, '60', 'after');
INSERT INTO document_sections VALUES (89, '566', 2354, '34', 'before');
INSERT INTO document_sections VALUES (93, '713', 4433, '91', 'before');
INSERT INTO document_sections VALUES (95, '621', 8805, '38', 'before');

CREATE TABLE document_sections_images (
       `section_id` INTEGER NOT NULL,
       `image_id` INTEGER NOT NULL,
       primary KEY (section_id, image_id)
);

INSERT INTO document_sections_images VALUES (93, 6);
INSERT INTO document_sections_images VALUES (86, 2);
INSERT INTO document_sections_images VALUES (27, 3);
INSERT INTO document_sections_images VALUES (12, 12);
INSERT INTO document_sections_images VALUES (19, 12);
INSERT INTO document_sections_images VALUES (38, 12);
INSERT INTO document_sections_images VALUES (89, 8);
INSERT INTO document_sections_images VALUES (23, 8);
INSERT INTO document_sections_images VALUES (40, 5);
INSERT INTO document_sections_images VALUES (19, 2);
INSERT INTO document_sections_images VALUES (62, 14);
INSERT INTO document_sections_images VALUES (21, 2);
INSERT INTO document_sections_images VALUES (86, 4);
INSERT INTO document_sections_images VALUES (15, 14);
INSERT INTO document_sections_images VALUES (54, 12);
INSERT INTO document_sections_images VALUES (38, 7);
INSERT INTO document_sections_images VALUES (15, 13);
INSERT INTO document_sections_images VALUES (27, 10);
INSERT INTO document_sections_images VALUES (40, 6);
INSERT INTO document_sections_images VALUES (19, 6);

CREATE TABLE document_structures (
       `document_structure_code` VARCHAR(255) PRIMARY KEY,
       `parent_document_structure_code` VARCHAR(255),
       `document_structure_description` VARCHAR(255)
);

INSERT INTO document_structures VALUES ('1', '1', 'Header');
INSERT INTO document_structures VALUES ('6', '1', 'Main section');
INSERT INTO document_structures VALUES ('8', '1', 'Bib');
INSERT INTO document_structures VALUES ('5', '6', 'Image section');
INSERT INTO document_structures VALUES ('9', '8', 'Author section');

CREATE TABLE documents (
       `document_code` VARCHAR(255) PRIMARY KEY,
       `document_structure_code` VARCHAR(255) NOT NULL,
       `document_type_code` VARCHAR(255) NOT NULL,
       `access_count` INTEGER,
       `document_name` VARCHAR(255)
);

INSERT INTO documents VALUES ('217', '8', 'Book', 1864, 'Learning English');
INSERT INTO documents VALUES ('621', '1', 'Paper', 8208, 'Research about Art history');
INSERT INTO documents VALUES ('958', '8', 'Book', 3769, 'Learning Database');
INSERT INTO documents VALUES ('961', '5', 'Advertisement', 6661, 'Summer Sails');
INSERT INTO documents VALUES ('989', '9', 'Book', 2910, 'Learning Japanese');
INSERT INTO documents VALUES ('930', '9', 'CV', 6345, 'David CV');
INSERT INTO documents VALUES ('928', '8', 'Book', 2045, 'How to cook pasta');
INSERT INTO documents VALUES ('510', '6', 'Paper', 3479, 'Humanity: a fact');
INSERT INTO documents VALUES ('706', '9', 'Advertisement', 8623, 'Winter Sails');
INSERT INTO documents VALUES ('465', '9', 'CV', 5924, 'John CV');
INSERT INTO documents VALUES ('713', '8', 'CV', 2294, 'Joe CV');
INSERT INTO documents VALUES ('566', '5', 'Advertisement', 3289, 'Spring Sails');
INSERT INTO documents VALUES ('349', '9', 'Book', 1219, 'Life about Claude Monet');
INSERT INTO documents VALUES ('675', '1', 'Advertisement', 7509, 'Fall Sails');
INSERT INTO documents VALUES ('714', '6', 'Paper', 9948, 'Relationships between History and Arts');

CREATE TABLE functional_areas (
       `functional_area_code` VARCHAR(255) PRIMARY KEY,
       `parent_functional_area_code` VARCHAR(255),
       `functional_area_description` VARCHAR(255) NOT NULL
);

INSERT INTO functional_areas VALUES ('8', '8', 'Signature');
INSERT INTO functional_areas VALUES ('1', '8', 'Acknowledgement');
INSERT INTO functional_areas VALUES ('9', '8', 'Keep blank');

CREATE TABLE images (
       `image_id` INTEGER PRIMARY KEY,
       `image_alt_text` VARCHAR(255),
       `image_name` VARCHAR(255),
       `image_url` VARCHAR(255)
);

INSERT INTO images VALUES (1, 'Lea', 'top1', 'http://www.rempelnader.com/1.jpg');
INSERT INTO images VALUES (2, 'Arden', 'top2', 'http://connellykertzmann.org/1.jpg');
INSERT INTO images VALUES (3, 'Mohamed', 'top3', 'http://www.bernierconnelly.com/1.jpg');
INSERT INTO images VALUES (4, 'Chaya', 'top4', 'http://abernathyboehm.com/1.jpg');
INSERT INTO images VALUES (5, 'Percival', 'chapter1', 'http://gaylord.info/1.jpg');
INSERT INTO images VALUES (6, 'Lincoln', 'chapter2', 'http://www.hellerreinger.com/1.jpg');
INSERT INTO images VALUES (7, 'Camylle', 'chapter3', 'http://faycummerata.net/1.jpg');
INSERT INTO images VALUES (8, 'Ashtyn', 'chapter4', 'http://haleychamplin.net/1.jpg');
INSERT INTO images VALUES (9, 'Filomena', 'chapter5', 'http://www.fritsch.net/1.jpg');
INSERT INTO images VALUES (10, 'Jeanette', 'data1', 'http://sauer.com/1.jpg');
INSERT INTO images VALUES (11, 'Name', 'data2', 'http://www.heller.com/1.jpg');
INSERT INTO images VALUES (12, 'Marianna', 'data3', 'http://www.hermann.com/1.jpg');
INSERT INTO images VALUES (13, 'Stephen', 'data4', 'http://rowelakin.com/1.jpg');
INSERT INTO images VALUES (14, 'Miller', 'data5', 'http://andersonluettgen.net/1.jpg');
INSERT INTO images VALUES (15, 'Trycia', 'data6', 'http://www.beahan.biz/1.jpg');

CREATE TABLE roles (
       `role_code` VARCHAR(255) PRIMARY KEY,
       `role_description` VARCHAR(255)
);

INSERT INTO roles VALUES ('DBA', 'Database Administrator');
INSERT INTO roles VALUES ('PROJ-MGR', 'Project Manager');

CREATE TABLE users (
       `user_id` INTEGER PRIMARY KEY,
       `role_code` VARCHAR(255) NOT NULL,
       `user_name` VARCHAR(255),
       `user_login` VARCHAR(255),
       `password` VARCHAR(255)
);

INSERT INTO users VALUES (1, 'PROJ-MGR', 'dickens.elta', '0', 'e72b5a2d50b39a8760764a5f7a9d68ca2f076877');
INSERT INTO users VALUES (2, 'DBA', 'tremblay.raheem', '1', '9bc25a040d5647ced5ec32e1a455e90fafc10bcb');
INSERT INTO users VALUES (3, 'DBA', 'lynn.haley', '0', '90db8f51449e6c39e2a01f0b649d5a92fe76bbbb');
INSERT INTO users VALUES (4, 'PROJ-MGR', 'ycremin', '0', 'f6977378f409f5d2d230016a6678a582e14f43b0');
INSERT INTO users VALUES (5, 'PROJ-MGR', 'larson.vesta', '1', 'da383455a05a824606c54e99f671c4d6a2ddae26');
INSERT INTO users VALUES (6, 'DBA', 'amelie53', '0', '6aa66440864ff8143fe7dee5940a6af3460bad07');
INSERT INTO users VALUES (7, 'DBA', 'jacklyn.schmitt', '1', '3f6affa583bfdf7fac6faeb2ca418431909d4b39');
INSERT INTO users VALUES (8, 'PROJ-MGR', 'joanne.deckow', '0', '20241478f890508ac47870cfba472e1db04a71ca');
INSERT INTO users VALUES (9, 'PROJ-MGR', 'dickinson.lenora', '0', 'a0fe5434a5f4c218e37b0082f2408b357feb0fa6');
INSERT INTO users VALUES (10, 'DBA', 'heller.harley', '1', '11af7569a5c1e8b455add5755e18131be2ac8636');
INSERT INTO users VALUES (11, 'DBA', 'roger.o''conner', '0', '3d478d7056d6417966f6b1676f6ec81b3094f44f');
INSERT INTO users VALUES (12, 'DBA', 'gussie00', '1', '75f7b5ed8e70e86467155e003ccda6fce1011c29');
INSERT INTO users VALUES (13, 'PROJ-MGR', 'johanna.fisher', '1', '1fb26eea854962d41512827bf90a5b7ce4b359d8');
INSERT INTO users VALUES (14, 'DBA', 'faye30', '0', '27cca8f94136f0e8971b5ca555a21ff756871b27');
INSERT INTO users VALUES (15, 'PROJ-MGR', 'glenna.simonis', '1', '95f489fc0921bbb3e7d661a550ae208b88d9b11a');

COMMIT;