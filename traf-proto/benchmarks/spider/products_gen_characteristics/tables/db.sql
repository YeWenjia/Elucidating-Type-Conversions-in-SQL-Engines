BEGIN;

CREATE TABLE characteristics (
       `characteristic_id` INTEGER PRIMARY KEY,
       `characteristic_type_code` VARCHAR(255) NOT NULL,
       `characteristic_data_type` VARCHAR(255),
       `characteristic_name` VARCHAR(255),
       `other_characteristic_details` VARCHAR(255)
);

INSERT INTO characteristics VALUES (1, 'Grade', 'numquam', 'slow', NULL);
INSERT INTO characteristics VALUES (2, 'Grade', 'doloribus', 'fast', NULL);
INSERT INTO characteristics VALUES (3, 'Purity', 'rem', 'warm', NULL);
INSERT INTO characteristics VALUES (4, 'Grade', 'aut', 'hot', NULL);
INSERT INTO characteristics VALUES (5, 'Purity', 'impedit', 'hot', NULL);
INSERT INTO characteristics VALUES (6, 'Purity', 'qui', 'warm', NULL);
INSERT INTO characteristics VALUES (7, 'Grade', 'et', 'cool', NULL);
INSERT INTO characteristics VALUES (8, 'Grade', 'dolores', 'cool', NULL);
INSERT INTO characteristics VALUES (9, 'Grade', 'quam', 'cool', NULL);
INSERT INTO characteristics VALUES (10, 'Grade', 'velit', 'fast', NULL);
INSERT INTO characteristics VALUES (11, 'Purity', 'at', 'fast', NULL);
INSERT INTO characteristics VALUES (12, 'Grade', 'totam', 'error', NULL);
INSERT INTO characteristics VALUES (13, 'Purity', 'mollitia', 'slow', NULL);
INSERT INTO characteristics VALUES (14, 'Purity', 'placeat', 'slow', NULL);
INSERT INTO characteristics VALUES (15, 'Grade', 'facere', 'slow', NULL);

CREATE TABLE product_characteristics (
       `product_id` INTEGER NOT NULL,
       `characteristic_id` INTEGER NOT NULL,
       `product_characteristic_value` VARCHAR(255)
);

INSERT INTO product_characteristics VALUES (13, 13, 'low');
INSERT INTO product_characteristics VALUES (11, 2, 'low');
INSERT INTO product_characteristics VALUES (5, 15, 'low');
INSERT INTO product_characteristics VALUES (1, 13, 'low');
INSERT INTO product_characteristics VALUES (7, 12, 'low');
INSERT INTO product_characteristics VALUES (11, 6, 'low');
INSERT INTO product_characteristics VALUES (7, 2, 'medium');
INSERT INTO product_characteristics VALUES (12, 10, 'medium');
INSERT INTO product_characteristics VALUES (8, 11, 'high');
INSERT INTO product_characteristics VALUES (14, 4, 'medium');
INSERT INTO product_characteristics VALUES (11, 3, 'medium');
INSERT INTO product_characteristics VALUES (6, 15, 'high');
INSERT INTO product_characteristics VALUES (11, 3, 'high');
INSERT INTO product_characteristics VALUES (6, 10, 'high');
INSERT INTO product_characteristics VALUES (12, 2, 'high');

CREATE TABLE products (
       `product_id` INTEGER PRIMARY KEY,
       `color_code` VARCHAR(255) NOT NULL,
       `product_category_code` VARCHAR(255) NOT NULL,
       `product_name` VARCHAR(255),
       `typical_buying_price` VARCHAR(255),
       `typical_selling_price` VARCHAR(255),
       `product_description` VARCHAR(255),
       `other_product_details` VARCHAR(255)
);

INSERT INTO products VALUES (1, '4', 'Spices', 'cumin', '', '2878.3', 'et', NULL);
INSERT INTO products VALUES (2, '2', 'Spices', 'peper', '352447.2874677', '1892070.2803543', 'rerum', NULL);
INSERT INTO products VALUES (3, '9', 'Herbs', 'basil', '503.8431967', '0.1859512', 'officia', NULL);
INSERT INTO products VALUES (4, '1', 'Herbs', 'borage', '', '10377614.847385', 'blanditiis', NULL);
INSERT INTO products VALUES (5, '4', 'Spices', 'chili', '', '39446', 'eius', NULL);
INSERT INTO products VALUES (6, '4', 'Seeds', 'ginger', '5.578', '52735.6101', 'doloribus', NULL);
INSERT INTO products VALUES (7, '9', 'Seeds', 'sesame', '1284268.0659', '68205825.7', 'et', NULL);
INSERT INTO products VALUES (8, '9', 'Herbs', 'caraway', '24493', '', 'nulla', NULL);
INSERT INTO products VALUES (9, '2', 'Herbs', 'catnip', '12008702.623', '21577.891642', 'vel', NULL);
INSERT INTO products VALUES (10, '5', 'Seeds', 'flax', '339404395.7', '59622629.74', 'et', NULL);
INSERT INTO products VALUES (11, '7', 'Herbs', 'chervil', '', '', 'minus', NULL);
INSERT INTO products VALUES (12, '4', 'Seeds', 'voluptatem', '162', '149', 'officia', NULL);
INSERT INTO products VALUES (13, '5', 'Spices', 'cinnam', '1686539.4', '17595111.4', 'nisi', NULL);
INSERT INTO products VALUES (14, '4', 'Seeds', 'lotus', '43221310.465574', '63589.4054376', 'exercitationem', NULL);
INSERT INTO products VALUES (15, '2', 'Herbs', 'laurel', '', '57857', 'ut', NULL);

CREATE TABLE ref_characteristic_types (
       `characteristic_type_code` VARCHAR(255) PRIMARY KEY,
       `characteristic_type_description` VARCHAR(255)
);

INSERT INTO ref_characteristic_types VALUES ('Grade', 'Grade');
INSERT INTO ref_characteristic_types VALUES ('Purity', 'Purity');

CREATE TABLE ref_colors (
       `color_code` VARCHAR(255) PRIMARY KEY,
       `color_description` VARCHAR(255)
);

INSERT INTO ref_colors VALUES ('9', 'red');
INSERT INTO ref_colors VALUES ('5', 'green');
INSERT INTO ref_colors VALUES ('1', 'yellow');
INSERT INTO ref_colors VALUES ('4', 'blue');
INSERT INTO ref_colors VALUES ('7', 'black');
INSERT INTO ref_colors VALUES ('2', 'white');
INSERT INTO ref_colors VALUES ('8', 'purple');
INSERT INTO ref_colors VALUES ('3', 'gray');

CREATE TABLE ref_product_categories (
       `product_category_code` VARCHAR(255) PRIMARY KEY,
       `product_category_description` VARCHAR(255),
       `unit_of_measure` VARCHAR(255)
);

INSERT INTO ref_product_categories VALUES ('Herbs', 'Herbs', 'Handful             ');
INSERT INTO ref_product_categories VALUES ('Seeds', 'Seeds', 'Weight - pound,kilo.');
INSERT INTO ref_product_categories VALUES ('Spices', 'Spices', 'Weight - pound,kilo.');

COMMIT;