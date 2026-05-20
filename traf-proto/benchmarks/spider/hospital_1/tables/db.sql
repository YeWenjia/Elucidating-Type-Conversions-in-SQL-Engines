BEGIN;

CREATE TABLE physician (
       employeeid INTEGER NOT NULL,
       name VARCHAR(255) NOT NULL,
       position VARCHAR(255) NOT NULL,
       ssn INTEGER NOT NULL,
       constraint pk_physician PRIMARY KEY(EmployeeID)
);

INSERT INTO physician VALUES (1, 'John Dorian', 'Staff Internist', 111111111);
INSERT INTO physician VALUES (2, 'Elliot Reid', 'Attending Physician', 222222222);
INSERT INTO physician VALUES (3, 'Christopher Turk', 'Surgical Attending Physician', 333333333);
INSERT INTO physician VALUES (4, 'Percival Cox', 'Senior Attending Physician', 444444444);
INSERT INTO physician VALUES (5, 'Bob Kelso', 'Head Chief of Medicine', 555555555);
INSERT INTO physician VALUES (6, 'Todd Quinlan', 'Surgical Attending Physician', 666666666);
INSERT INTO physician VALUES (7, 'John Wen', 'Surgical Attending Physician', 777777777);
INSERT INTO physician VALUES (8, 'Keith Dudemeister', 'MD Resident', 888888888);
INSERT INTO physician VALUES (9, 'Molly Clock', 'Attending Psychiatrist', 999999999);

CREATE TABLE department (
       departmentid INTEGER NOT NULL,
       name VARCHAR(255) NOT NULL,
       head INTEGER NOT NULL,
       constraint pk_Department PRIMARY KEY(DepartmentID),
       constraint fk_Department_Physician_EmployeeID FOREIGN KEY(Head) REFERENCES Physician(EmployeeID)
);

INSERT INTO department VALUES (1, 'General Medicine', 4);
INSERT INTO department VALUES (2, 'Surgery', 7);
INSERT INTO department VALUES (3, 'Psychiatry', 9);


CREATE TABLE patient (
       ssn INTEGER PRIMARY KEY NOT NULL,
       name VARCHAR(255) NOT NULL,
       address VARCHAR(255) NOT NULL,
       phone VARCHAR(255) NOT NULL,
       insuranceid INTEGER NOT NULL,
       pcp INTEGER NOT NULL,
       constraint fk_Patient_Physician_EmployeeID FOREIGN KEY(PCP) REFERENCES Physician(EmployeeID)
);

INSERT INTO patient VALUES (100000001, 'John Smith', '42 Foobar Lane', '555-0256', 68476213, 1);
INSERT INTO patient VALUES (100000002, 'Grace Ritchie', '37 Snafu Drive', '555-0512', 36546321, 2);
INSERT INTO patient VALUES (100000003, 'Random J. Patient', '101 Omgbbq Street', '555-1204', 65465421, 2);
INSERT INTO patient VALUES (100000004, 'Dennis Doe', '1100 Foobaz Avenue', '555-2048', 68421879, 3);



CREATE TABLE nurse (
       employeeid INTEGER PRIMARY KEY NOT NULL,
       name VARCHAR(255) NOT NULL,
       position VARCHAR(255) NOT NULL,
       registered BOOLEAN NOT NULL,
       ssn INTEGER NOT NULL
);

INSERT INTO nurse VALUES (101, 'Carla Espinosa', 'Head Nurse', True, 111111110);
INSERT INTO nurse VALUES (102, 'Laverne Roberts', 'Nurse', True, 222222220);
INSERT INTO nurse VALUES (103, 'Paul Flowers', 'Nurse', False, 333333330);


CREATE TABLE affiliated_with (
       physician INTEGER NOT NULL,
       department INTEGER NOT NULL,
       primaryaffiliation BOOLEAN NOT NULL,
       constraint fk_Affiliated_With_Physician_EmployeeID FOREIGN KEY(Physician) REFERENCES Physician(EmployeeID),
       constraint fk_Affiliated_With_Department_DepartmentID FOREIGN KEY(Department) REFERENCES Department(DepartmentID),
       primary KEY (physician, department)
);

INSERT INTO affiliated_with VALUES (1, 1, True);
INSERT INTO affiliated_with VALUES (2, 1, True);
INSERT INTO affiliated_with VALUES (3, 1, False);
INSERT INTO affiliated_with VALUES (3, 2, True);
INSERT INTO affiliated_with VALUES (4, 1, True);
INSERT INTO affiliated_with VALUES (5, 1, True);
INSERT INTO affiliated_with VALUES (6, 2, True);
INSERT INTO affiliated_with VALUES (7, 1, False);
INSERT INTO affiliated_with VALUES (7, 2, True);
INSERT INTO affiliated_with VALUES (8, 1, True);
INSERT INTO affiliated_with VALUES (9, 3, True);

CREATE TABLE appointment (
       appointmentid INTEGER PRIMARY KEY NOT NULL,
       patient INTEGER NOT NULL,
       prepnurse INTEGER,
       physician INTEGER NOT NULL,
       start DATETIME NOT NULL,
       end DATETIME NOT NULL,
       examinationroom TEXT NOT NULL,
       constraint fk_Appointment_Patient_SSN FOREIGN KEY(Patient) REFERENCES Patient(SSN),
       constraint fk_Appointment_Nurse_EmployeeID FOREIGN KEY(PrepNurse) REFERENCES Nurse(EmployeeID),
       constraint fk_Appointment_Physician_EmployeeID FOREIGN KEY(Physician) REFERENCES Physician(EmployeeID)
);

INSERT INTO appointment VALUES (13216584, 100000001, 101, 1, '2008-04-24 10:00', '2008-04-24 11:00', 'A');
INSERT INTO appointment VALUES (26548913, 100000002, 101, 2, '2008-04-24 10:00', '2008-04-24 11:00', 'B');
INSERT INTO appointment VALUES (36549879, 100000001, 102, 1, '2008-04-25 10:00', '2008-04-25 11:00', 'A');
INSERT INTO appointment VALUES (46846589, 100000004, 103, 4, '2008-04-25 10:00', '2008-04-25 11:00', 'B');
INSERT INTO appointment VALUES (59871321, 100000004, NULL, 4, '2008-04-26 10:00', '2008-04-26 11:00', 'C');
INSERT INTO appointment VALUES (69879231, 100000003, 103, 2, '2008-04-26 11:00', '2008-04-26 12:00', 'C');
INSERT INTO appointment VALUES (76983231, 100000001, NULL, 3, '2008-04-26 12:00', '2008-04-26 13:00', 'C');
INSERT INTO appointment VALUES (86213939, 100000004, 102, 9, '2008-04-27 10:00', '2008-04-21 11:00', 'A');
INSERT INTO appointment VALUES (93216548, 100000002, 101, 2, '2008-04-27 10:00', '2008-04-27 11:00', 'B');

CREATE TABLE block (
       blockfloor INTEGER NOT NULL,
       blockcode INTEGER NOT NULL,
       primary KEY (blockfloor, blockcode)
);

INSERT INTO block VALUES (1, 1);
INSERT INTO block VALUES (1, 2);
INSERT INTO block VALUES (1, 3);
INSERT INTO block VALUES (2, 1);
INSERT INTO block VALUES (2, 2);
INSERT INTO block VALUES (2, 3);
INSERT INTO block VALUES (3, 1);
INSERT INTO block VALUES (3, 2);
INSERT INTO block VALUES (3, 3);
INSERT INTO block VALUES (4, 1);
INSERT INTO block VALUES (4, 2);
INSERT INTO block VALUES (4, 3);



CREATE TABLE medication (
       code INTEGER PRIMARY KEY NOT NULL,
       name VARCHAR(255) NOT NULL,
       brand VARCHAR(255) NOT NULL,
       description VARCHAR(255) NOT NULL
);

INSERT INTO medication VALUES (1, 'Procrastin-X', 'X', 'N/A');
INSERT INTO medication VALUES (2, 'Thesisin', 'Foo Labs', 'N/A');
INSERT INTO medication VALUES (3, 'Awakin', 'Bar Laboratories', 'N/A');
INSERT INTO medication VALUES (4, 'Crescavitin', 'Baz Industries', 'N/A');
INSERT INTO medication VALUES (5, 'Melioraurin', 'Snafu Pharmaceuticals', 'N/A');



CREATE TABLE on_call (
       nurse INTEGER NOT NULL,
       blockfloor INTEGER NOT NULL,
       blockcode INTEGER NOT NULL,
       oncallstart DATETIME NOT NULL,
       oncallend DATETIME NOT NULL,
       primary KEY (nurse, blockfloor, blockcode, oncallstart, oncallend),
       constraint fk_OnCall_Nurse_EmployeeID FOREIGN KEY(Nurse) REFERENCES Nurse(EmployeeID),
       constraint fk_OnCall_Block_Floor FOREIGN KEY(BlockFloor, BlockCode) REFERENCES Block(BlockFloor, BlockCode)
);

INSERT INTO on_call VALUES (101, 1, 1, '2008-11-04 11:00', '2008-11-04 19:00');
INSERT INTO on_call VALUES (101, 1, 2, '2008-11-04 11:00', '2008-11-04 19:00');
INSERT INTO on_call VALUES (102, 1, 3, '2008-11-04 11:00', '2008-11-04 19:00');
INSERT INTO on_call VALUES (103, 1, 1, '2008-11-04 19:00', '2008-11-05 03:00');
INSERT INTO on_call VALUES (103, 1, 2, '2008-11-04 19:00', '2008-11-05 03:00');
INSERT INTO on_call VALUES (103, 1, 3, '2008-11-04 19:00', '2008-11-05 03:00');





CREATE TABLE prescribes (
       physician INTEGER NOT NULL,
       patient INTEGER NOT NULL,
       medication INTEGER NOT NULL,
       date DATETIME NOT NULL,
       appointment INTEGER,
       dose VARCHAR(255) NOT NULL,
       primary KEY (physician, patient, medication, date),
       constraint fk_Prescribes_Physician_EmployeeID FOREIGN KEY(Physician) REFERENCES Physician(EmployeeID),
       constraint fk_Prescribes_Patient_SSN FOREIGN KEY(Patient) REFERENCES Patient(SSN),
       constraint fk_Prescribes_Medication_Code FOREIGN KEY(Medication) REFERENCES Medication(Code),
       constraint fk_Prescribes_Appointment_AppointmentID FOREIGN KEY(Appointment) REFERENCES Appointment(AppointmentID)
);

INSERT INTO prescribes VALUES (1, 100000001, 1, '2008-04-24 10:47', 13216584, '5');
INSERT INTO prescribes VALUES (9, 100000004, 2, '2008-04-27 10:53', 86213939, '10');
INSERT INTO prescribes VALUES (9, 100000004, 2, '2008-04-30 16:53', NULL, '5');

CREATE TABLE procedures (
       code INTEGER PRIMARY KEY NOT NULL,
       name VARCHAR(255) NOT NULL,
       cost REAL NOT NULL
);

INSERT INTO procedures VALUES (1, 'Reverse Rhinopodoplasty', 1500.0);
INSERT INTO procedures VALUES (2, 'Obtuse Pyloric Recombobulation', 3750.0);
INSERT INTO procedures VALUES (3, 'Folded Demiophtalmectomy', 4500.0);
INSERT INTO procedures VALUES (4, 'Complete Walletectomy', 10000.0);
INSERT INTO procedures VALUES (5, 'Obfuscated Dermogastrotomy', 4899.0);
INSERT INTO procedures VALUES (6, 'Reversible Pancreomyoplasty', 5600.0);
INSERT INTO procedures VALUES (7, 'Follicular Demiectomy', 25.0);

CREATE TABLE room (
       roomnumber INTEGER PRIMARY KEY NOT NULL,
       roomtype VARCHAR(255) NOT NULL,
       blockfloor INTEGER NOT NULL,
       blockcode INTEGER NOT NULL,
       unavailable BOOLEAN NOT NULL,
       constraint fk_Room_Block_PK FOREIGN KEY(BlockFloor, BlockCode) REFERENCES Block(BlockFloor, BlockCode)
);

INSERT INTO room VALUES (101, 'Single', 1, 1, False);
INSERT INTO room VALUES (102, 'Single', 1, 1, False);
INSERT INTO room VALUES (103, 'Single', 1, 1, False);
INSERT INTO room VALUES (111, 'Single', 1, 2, False);
INSERT INTO room VALUES (112, 'Single', 1, 2, True);
INSERT INTO room VALUES (113, 'Single', 1, 2, False);
INSERT INTO room VALUES (121, 'Single', 1, 3, False);
INSERT INTO room VALUES (122, 'Single', 1, 3, False);
INSERT INTO room VALUES (123, 'Single', 1, 3, False);
INSERT INTO room VALUES (201, 'Single', 2, 1, True);
INSERT INTO room VALUES (202, 'Single', 2, 1, False);
INSERT INTO room VALUES (203, 'Single', 2, 1, False);
INSERT INTO room VALUES (211, 'Single', 2, 2, False);
INSERT INTO room VALUES (212, 'Single', 2, 2, False);
INSERT INTO room VALUES (213, 'Single', 2, 2, True);
INSERT INTO room VALUES (221, 'Single', 2, 3, False);
INSERT INTO room VALUES (222, 'Single', 2, 3, False);
INSERT INTO room VALUES (223, 'Single', 2, 3, False);
INSERT INTO room VALUES (301, 'Single', 3, 1, False);
INSERT INTO room VALUES (302, 'Single', 3, 1, True);
INSERT INTO room VALUES (303, 'Single', 3, 1, False);
INSERT INTO room VALUES (311, 'Single', 3, 2, False);
INSERT INTO room VALUES (312, 'Single', 3, 2, False);
INSERT INTO room VALUES (313, 'Single', 3, 2, False);
INSERT INTO room VALUES (321, 'Single', 3, 3, True);
INSERT INTO room VALUES (322, 'Single', 3, 3, False);
INSERT INTO room VALUES (323, 'Single', 3, 3, False);
INSERT INTO room VALUES (401, 'Single', 4, 1, False);
INSERT INTO room VALUES (402, 'Single', 4, 1, True);
INSERT INTO room VALUES (403, 'Single', 4, 1, False);
INSERT INTO room VALUES (411, 'Single', 4, 2, False);
INSERT INTO room VALUES (412, 'Single', 4, 2, False);
INSERT INTO room VALUES (413, 'Single', 4, 2, False);
INSERT INTO room VALUES (421, 'Single', 4, 3, True);
INSERT INTO room VALUES (422, 'Single', 4, 3, False);
INSERT INTO room VALUES (423, 'Single', 4, 3, False);

CREATE TABLE stay (
       stayid INTEGER PRIMARY KEY NOT NULL,
       patient INTEGER NOT NULL,
       room INTEGER NOT NULL,
       staystart DATETIME NOT NULL,
       stayend DATETIME NOT NULL,
       constraint fk_Stay_Patient_SSN FOREIGN KEY(Patient) REFERENCES Patient(SSN),
       constraint fk_Stay_Room_Number FOREIGN KEY(Room) REFERENCES Room(RoomNumber)
);

INSERT INTO stay VALUES (3215, 100000001, 111, '2008-05-01', '2008-05-04');
INSERT INTO stay VALUES (3216, 100000003, 123, '2008-05-03', '2008-05-14');
INSERT INTO stay VALUES (3217, 100000004, 112, '2008-05-02', '2008-05-03');

CREATE TABLE trained_in (
       physician INTEGER NOT NULL,
       treatment INTEGER NOT NULL,
       certificationdate DATETIME NOT NULL,
       certificationexpires DATETIME NOT NULL,
       constraint fk_Trained_In_Physician_EmployeeID FOREIGN KEY(Physician) REFERENCES Physician(EmployeeID),
       constraint fk_Trained_In_Procedures_Code FOREIGN KEY(Treatment) REFERENCES Procedures(Code),
       primary KEY (physician, treatment)
);

INSERT INTO trained_in VALUES (3, 1, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (3, 2, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (3, 5, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (3, 6, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (3, 7, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (6, 2, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (6, 5, '2007-01-01', '2007-12-31');
INSERT INTO trained_in VALUES (6, 6, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (7, 1, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (7, 2, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (7, 3, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (7, 4, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (7, 5, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (7, 6, '2008-01-01', '2008-12-31');
INSERT INTO trained_in VALUES (7, 7, '2008-01-01', '2008-12-31');

CREATE TABLE undergoes (
       patient INTEGER NOT NULL,
       procedures INTEGER NOT NULL,
       stay INTEGER NOT NULL,
       dateundergoes DATETIME NOT NULL,
       physician INTEGER NOT NULL,
       assistingnurse INTEGER,
       primary KEY (patient, procedures, stay, dateundergoes),
       constraint fk_Undergoes_Patient_SSN FOREIGN KEY(Patient) REFERENCES Patient(SSN),
       constraint fk_Undergoes_Procedures_Code FOREIGN KEY(Procedures) REFERENCES Procedures(Code),
       constraint fk_Undergoes_Stay_StayID FOREIGN KEY(Stay) REFERENCES Stay(StayID),
       constraint fk_Undergoes_Physician_EmployeeID FOREIGN KEY(Physician) REFERENCES Physician(EmployeeID)
);

INSERT INTO undergoes VALUES (100000001, 6, 3215, '2008-05-02', 3, 101);
INSERT INTO undergoes VALUES (100000001, 2, 3215, '2008-05-03', 7, 101);
INSERT INTO undergoes VALUES (100000004, 1, 3217, '2008-05-07', 3, 102);
INSERT INTO undergoes VALUES (100000004, 5, 3217, '2008-05-09', 6, 105);
INSERT INTO undergoes VALUES (100000001, 7, 3217, '2008-05-10', 7, 101);


COMMIT;