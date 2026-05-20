BEGIN;

CREATE TABLE assignedto (
       scientist int not null,
       project VARCHAR(255) not null,
       primary KEY (scientist, project)
);

INSERT INTO assignedto VALUES (123234877, 'AeH1');
INSERT INTO assignedto VALUES (152934485, 'AeH3');
INSERT INTO assignedto VALUES (222364883, 'Ast3');
INSERT INTO assignedto VALUES (326587417, 'Ast3');
INSERT INTO assignedto VALUES (332154719, 'Bte1');
INSERT INTO assignedto VALUES (546523478, 'Che1');
INSERT INTO assignedto VALUES (631231482, 'Ast3');
INSERT INTO assignedto VALUES (654873219, 'Che1');
INSERT INTO assignedto VALUES (745685214, 'AeH3');
INSERT INTO assignedto VALUES (845657245, 'Ast1');
INSERT INTO assignedto VALUES (845657246, 'Ast2');
INSERT INTO assignedto VALUES (332569843, 'AeH4');

CREATE TABLE projects (
       code VARCHAR(255),
       name VARCHAR(255) not null,
       hours int,
       primary KEY (code)
);

INSERT INTO projects VALUES ('AeH1', 'Winds: Studying Bernoullis Principle', 156);
INSERT INTO projects VALUES ('AeH2', 'Aerodynamics and Bridge Design', 189);
INSERT INTO projects VALUES ('AeH3', 'Aerodynamics and Gas Mileage', 256);
INSERT INTO projects VALUES ('AeH4', 'Aerodynamics and Ice Hockey', 789);
INSERT INTO projects VALUES ('AeH5', 'Aerodynamics of a Football', 98);
INSERT INTO projects VALUES ('AeH6', 'Aerodynamics of Air Hockey', 89);
INSERT INTO projects VALUES ('Ast1', 'A Matter of Time', 112);
INSERT INTO projects VALUES ('Ast2', 'A Puzzling Parallax', 299);
INSERT INTO projects VALUES ('Ast3', 'Build Your Own Telescope', 6546);
INSERT INTO projects VALUES ('Bte1', 'Juicy: Extracting Apple Juice with Pectinase', 321);
INSERT INTO projects VALUES ('Bte2', 'A Magnetic Primer Designer', 9684);
INSERT INTO projects VALUES ('Bte3', 'Bacterial Transformation Efficiency', 321);
INSERT INTO projects VALUES ('Che1', 'A Silver-Cleaning Battery', 545);
INSERT INTO projects VALUES ('Che2', 'A Soluble Separation Solution', 778);

CREATE TABLE scientists (
       ssn int,
       name VARCHAR(255) not null,
       primary KEY (ssn)
);

INSERT INTO scientists VALUES (123234877, 'Michael Rogers');
INSERT INTO scientists VALUES (152934485, 'Anand Manikutty');
INSERT INTO scientists VALUES (222364883, 'Carol Smith');
INSERT INTO scientists VALUES (326587417, 'Joe Stevens');
INSERT INTO scientists VALUES (332154719, 'Mary-Anne Foster');
INSERT INTO scientists VALUES (332569843, 'George ODonnell');
INSERT INTO scientists VALUES (546523478, 'John Doe');
INSERT INTO scientists VALUES (631231482, 'David Smith');
INSERT INTO scientists VALUES (654873219, 'Zacary Efron');
INSERT INTO scientists VALUES (745685214, 'Eric Goldsmith');
INSERT INTO scientists VALUES (845657245, 'Elizabeth Doe');
INSERT INTO scientists VALUES (845657246, 'Kumar Swamy');

COMMIT;