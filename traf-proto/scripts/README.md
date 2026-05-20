# Scripts

Utility scripts for the SQL interpreter project.

---

## process_all_spider.py

Batch-processes all Spider benchmark folders by converting SQLite databases to PostgreSQL and normalizing queries.

### What It Does

For each folder in `benchmarks/spider/`:

1. **Converts SQLite to PostgreSQL**: Runs `sqlite_to_sql.py` to convert `db.sqlite` → `db.sql`
2. **Normalizes queries**: Runs `postgres_normalize.py` to make SQL PostgreSQL-compatible
3. **Deletes CSV files**: Removes all CSV files from `tables/` folders

### Usage

```bash
# Dry run - preview what would be processed (no changes)
python scripts/process_all_spider.py --dry-run

# Actually process all folders
python scripts/process_all_spider.py
```

### Example Output

```
Found 145 folders in benchmarks/spider

================================================================================
Processing: activity_1
================================================================================

[1/2] Converting SQLite to PostgreSQL SQL...
  ✓ Converted db.sqlite → db.sql (2 tables, 45 rows)

[2/2] Normalizing queries and deleting CSVs...
  ✓ Normalized 15 YAML files
  ✓ Deleted 3 CSV files
✅ Completed: activity_1

...

================================================================================
SUMMARY
================================================================================
Total folders: 145
✅ Successfully processed: 140
⚠️  Skipped: 5
❌ Errors: 0
```

### When To Use

- **Initial setup**: First time setting up Spider benchmarks for PostgreSQL
- **After updates**: When Spider dataset is updated and needs re-processing
- **Sanity check**: Use `--dry-run` to verify which folders would be affected

---

## postgres_normalize.py

Normalizes SQL queries in YAML benchmark files to be PostgreSQL-friendly and cleans up CSV files.

### Features

- **Lowercase identifiers**: Converts all table and column names to lowercase
- **Single quotes for strings**: Converts double-quoted string literals to single quotes
- **Preserves SQL keywords**: Keeps SELECT, FROM, WHERE, etc. in original case
- **Safe transformation**: Protects string literals during identifier lowercasing
- **Batch processing**: Process all YAML files in a folder at once
- **CSV cleanup**: Automatically deletes all CSV files from the tables/ subfolder

### Usage

#### Basic Usage

Normalize all YAML files in a Spider benchmark folder:

```bash
# Dry run - preview changes without modifying files or deleting CSVs
python scripts/postgres_normalize.py apartment_rentals --dry-run

# Apply changes and delete CSV files
python scripts/postgres_normalize.py apartment_rentals
```

#### Example Transformation

**Before:**

```sql
SELECT booking_start_date
FROM Apartment_Bookings
WHERE booking_status = "Confirmed"
```

**After:**

```sql
SELECT booking_start_date
FROM apartment_bookings
WHERE booking_status = 'Confirmed'
```

### Options

- `folder`: Folder name relative to `benchmarks/spider/` (required)
- `--dry-run`: Show what would change without modifying files or deleting CSVs
- `--base-dir PATH`: Custom base directory (default: `benchmarks/spider`)

### What Gets Cleaned Up

After normalizing the SQL queries, the script also:

- **Deletes all CSV files** from the `tables/` subfolder (both input CSVs like `apartments.csv` and output CSVs like `0001.csv`)
- Keeps `db.sql` and `db.sqlite` files intact

This cleanup is safe because:

1. The `db.sql` file (from `sqlite_to_sql.py`) contains all the table data
2. The YAML files reference the database files, not the CSVs
3. The CSV files are no longer needed for PostgreSQL testing

### Examples

```bash
# Preview changes for apartment_rentals (safe - no modifications)
python scripts/postgres_normalize.py apartment_rentals --dry-run

# Apply changes to apartment_rentals (normalizes SQL + deletes CSVs)
python scripts/postgres_normalize.py apartment_rentals

# Use custom base directory
python scripts/postgres_normalize.py apartment_rentals --base-dir custom/path
```

---

## sqlite_to_sql.py

Converts SQLite `db.sqlite` files to PostgreSQL-compatible `db.sql` files with lowercase identifiers.

### Features

- **Lowercase tables and columns**: Converts all table and column names to lowercase for PostgreSQL compatibility
- **PostgreSQL data types**: Converts SQLite types to PostgreSQL equivalents (e.g., `DATETIME` → `TIMESTAMP`)
- **Generous string lengths**: Converts all `CHAR(n)` and `VARCHAR(n)` to `VARCHAR(255)` to prevent truncation errors
- **Single quotes for strings**: Uses single quotes for string literals as per SQL standard
- **Preserves relationships**: Maintains foreign key references with lowercase table/column names
- **Handles all data types**: NULL values, integers, floats, and strings (with proper quote escaping)
- **Batch processing**: Process single files or entire directory trees

### Data Type Conversions

| SQLite Type  | PostgreSQL Type       | Reason                                                |
| ------------ | --------------------- | ----------------------------------------------------- |
| `DATETIME`   | `TIMESTAMP`           | PostgreSQL doesn't have DATETIME type                 |
| `CHAR(n)`    | `VARCHAR(255)`        | SQLite doesn't enforce length, use generous size      |
| `VARCHAR(n)` | `VARCHAR(255)`        | SQLite doesn't enforce length, standardize to 255     |
| `BIT`        | `INTEGER`             | PostgreSQL BIT type incompatible with numeric inserts |
| `BOOL`       | `BOOLEAN`             | Standard PostgreSQL boolean type                      |
| `INTEGER`    | `INTEGER` (preserved) | Compatible                                            |
| `TEXT`       | `TEXT` (preserved)    | Compatible                                            |
| `REAL`       | `REAL` (preserved)    | Compatible                                            |

**Why use VARCHAR(255) for all string types?**  
SQLite doesn't enforce length constraints, so data often exceeds declared lengths. Rather than debugging individual truncation errors, we use a generous `VARCHAR(255)` for all character types. This ensures data loads successfully without sacrificing meaningful performance or storage.

**Why convert BIT to INTEGER?**  
SQLite's BIT type stores 0/1 as integers, but PostgreSQL's BIT type expects bit strings (e.g., B'1'). Converting to INTEGER avoids type mismatch errors and works seamlessly with existing numeric data.

Other types are preserved as-is.

### Usage

#### Single Folder

Convert one specific folder's `db.sqlite`:

```bash
python scripts/sqlite_to_sql.py benchmarks/spider/allergy_1/tables
```

Output: Creates `benchmarks/spider/allergy_1/tables/db.sql`

#### Multiple Folders

Convert multiple folders at once:

```bash
python scripts/sqlite_to_sql.py \
    benchmarks/spider/allergy_1/tables \
    benchmarks/spider/concert_singer/tables \
    benchmarks/spider/car_1/tables
```

#### Auto-Discovery Mode

Automatically find and convert all `db.sqlite` files in a directory tree:

```bash
# Convert all Spider datasets
python scripts/sqlite_to_sql.py --auto

# Or specify a custom base path
python scripts/sqlite_to_sql.py --auto --base-path benchmarks/spider
```

#### Using Shell Glob Patterns

Use shell wildcards to process multiple folders (zsh/bash will expand the pattern):

```bash
# Process all folders under benchmarks/spider/
python scripts/sqlite_to_sql.py benchmarks/spider/*/tables
```

### Example Output

**Before (SQLite schema):**

```sql
CREATE TABLE Allergy_Type (
    Allergy VARCHAR(20) PRIMARY KEY,
    AllergyType VARCHAR(20)
);

INSERT INTO Allergy_Type VALUES ("Eggs", "food");
```

**After (db.sql):**

```sql
CREATE TABLE allergy_type (
       allergy VARCHAR(20) PRIMARY KEY,
       allergytype VARCHAR(20)
);

INSERT INTO allergy_type VALUES ('Eggs', 'food');
```

### Command-Line Options

```
usage: sqlite_to_sql.py [-h] [--auto] [--base-path BASE_PATH] [paths ...]

Convert SQLite db.sqlite files to db.sql with lowercase identifiers

positional arguments:
  paths                 Paths to folders containing db.sqlite or to db.sqlite
                        files directly

optional arguments:
  -h, --help            show this help message and exit
  --auto                Auto-find all db.sqlite files in the given path
  --base-path BASE_PATH
                        Base path for --auto mode (default: benchmarks/spider)
```

### Requirements

- Python 3.6+
- Standard library only (no external dependencies)

### Notes

- The script preserves the original `db.sqlite` file (read-only operation)
- If `db.sql` already exists, it will be overwritten
- Foreign key relationships are preserved with lowercase references
- String values containing single quotes are properly escaped (`'` → `''`)
