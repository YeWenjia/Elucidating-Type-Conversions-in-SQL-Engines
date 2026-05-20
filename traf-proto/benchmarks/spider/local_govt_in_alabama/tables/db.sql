BEGIN;

CREATE TABLE events (
       event_id INTEGER NOT NULL,
       service_id INTEGER NOT NULL,
       event_details VARCHAR(255),
       primary KEY (event_id)
);

INSERT INTO events VALUES (3, 5, 'Success');
INSERT INTO events VALUES (8, 8, 'Success');
INSERT INTO events VALUES (13, 8, 'Fail');
INSERT INTO events VALUES (16, 2, 'Fail');
INSERT INTO events VALUES (17, 5, 'Fail');
INSERT INTO events VALUES (38, 6, 'Fail');
INSERT INTO events VALUES (40, 6, 'Fail');
INSERT INTO events VALUES (43, 8, 'Fail');
INSERT INTO events VALUES (48, 8, 'Fail');
INSERT INTO events VALUES (57, 5, 'Success');
INSERT INTO events VALUES (60, 2, 'Fail');
INSERT INTO events VALUES (74, 2, 'Success');
INSERT INTO events VALUES (80, 5, 'Success');
INSERT INTO events VALUES (95, 2, 'Fail');
INSERT INTO events VALUES (96, 2, 'Success');

CREATE TABLE participants (
       participant_id INTEGER NOT NULL,
       participant_type_code VARCHAR(255) NOT NULL,
       participant_details VARCHAR(255),
       primary KEY (participant_id)
);

INSERT INTO participants VALUES (9, 'Organizer', 'Karlee Batz');
INSERT INTO participants VALUES (26, 'Organizer', 'Vilma Schinner');
INSERT INTO participants VALUES (28, 'Organizer', 'Lupe Deckow');
INSERT INTO participants VALUES (36, 'Organizer', 'Kenyatta Kuhn');
INSERT INTO participants VALUES (37, 'Participant', 'Miss Kaci Lebsack');
INSERT INTO participants VALUES (38, 'Organizer', 'Macy Mayer DDS');
INSERT INTO participants VALUES (60, 'Participant', 'Dewitt Walter');
INSERT INTO participants VALUES (63, 'Participant', 'Prof. Michelle Maggio Jr.');
INSERT INTO participants VALUES (64, 'Participant', 'Dr. Jaydon Renner');
INSERT INTO participants VALUES (66, 'Participant', 'Justyn Lebsack');
INSERT INTO participants VALUES (75, 'Participant', 'Berniece Weimann');
INSERT INTO participants VALUES (86, 'Organizer', 'Neil Blick');
INSERT INTO participants VALUES (90, 'Participant', 'Dedrick Ebert');
INSERT INTO participants VALUES (96, 'Organizer', 'Miss Joyce Cremin');
INSERT INTO participants VALUES (98, 'Participant', 'Dr. Kris Deckow');

CREATE TABLE participants_in_events (
       event_id INTEGER NOT NULL,
       participant_id INTEGER NOT NULL,
       primary KEY (event_id, participant_id)
);

INSERT INTO participants_in_events VALUES (3, 26);
INSERT INTO participants_in_events VALUES (3, 66);
INSERT INTO participants_in_events VALUES (8, 86);
INSERT INTO participants_in_events VALUES (13, 64);
INSERT INTO participants_in_events VALUES (13, 90);
INSERT INTO participants_in_events VALUES (16, 60);
INSERT INTO participants_in_events VALUES (17, 37);
INSERT INTO participants_in_events VALUES (17, 66);
INSERT INTO participants_in_events VALUES (38, 66);
INSERT INTO participants_in_events VALUES (40, 37);
INSERT INTO participants_in_events VALUES (40, 86);
INSERT INTO participants_in_events VALUES (57, 90);
INSERT INTO participants_in_events VALUES (60, 26);
INSERT INTO participants_in_events VALUES (80, 36);
INSERT INTO participants_in_events VALUES (80, 66);
INSERT INTO participants_in_events VALUES (80, 96);
INSERT INTO participants_in_events VALUES (95, 63);
INSERT INTO participants_in_events VALUES (96, 90);

CREATE TABLE services (
       service_id INTEGER NOT NULL,
       service_type_code VARCHAR(255) NOT NULL,
       primary KEY (service_id)
);

INSERT INTO services VALUES (2, 'Marriage');
INSERT INTO services VALUES (5, 'Death Proof');
INSERT INTO services VALUES (6, 'Birth Proof');
INSERT INTO services VALUES (8, 'Property Change');

COMMIT;