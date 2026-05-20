BEGIN;

CREATE TABLE manufacturers (
       code INTEGER,
       name VARCHAR(255) NOT NULL,
       headquarter VARCHAR(255) NOT NULL,
       founder VARCHAR(255) NOT NULL,
       revenue REAL,
       primary KEY (code)
);

INSERT INTO manufacturers VALUES (1, 'Sony', 'Tokyo', 'Andy', 120.0);
INSERT INTO manufacturers VALUES (2, 'Creative Labs', 'Austin', 'Owen', 100.0);
INSERT INTO manufacturers VALUES (3, 'Hewlett-Packard', 'Los Angeles', 'James', 50.0);
INSERT INTO manufacturers VALUES (4, 'Iomega', 'Beijing', 'Mary', 200.0);
INSERT INTO manufacturers VALUES (5, 'Fujitsu', 'Taiwan', 'John', 130.0);
INSERT INTO manufacturers VALUES (6, 'Winchester', 'Paris', 'Robert', 30.0);

CREATE TABLE products (
       code INTEGER,
       name VARCHAR(255) NOT NULL,
       price DECIMAL NOT NULL,
       manufacturer INTEGER NOT NULL,
       primary KEY (code)
);

INSERT INTO products VALUES (1, 'Hard drive', 240, 5);
INSERT INTO products VALUES (2, 'Memory', 120, 6);
INSERT INTO products VALUES (3, 'ZIP drive', 150, 4);
INSERT INTO products VALUES (4, 'Floppy disk', 5, 6);
INSERT INTO products VALUES (5, 'Monitor', 240, 1);
INSERT INTO products VALUES (6, 'DVD drive', 180, 2);
INSERT INTO products VALUES (7, 'CD drive', 90, 2);
INSERT INTO products VALUES (8, 'Printer', 270, 3);
INSERT INTO products VALUES (9, 'Toner cartridge', 66, 3);
INSERT INTO products VALUES (10, 'DVD burner', 180, 2);
INSERT INTO products VALUES (11, 'DVD drive', 150, 3);

COMMIT;