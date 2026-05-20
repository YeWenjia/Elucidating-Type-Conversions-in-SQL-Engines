#!/bin/bash
# Drop all MySQL databases created by spider benchmark tests
mysql -u root -h localhost -P 3306 -e "
SELECT CONCAT('DROP DATABASE IF EXISTS \`', SCHEMA_NAME, '\`;')
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys', 'interpreter')
" -s -N | mysql -u root -h localhost -P 3306

echo "All spider MySQL databases dropped."
