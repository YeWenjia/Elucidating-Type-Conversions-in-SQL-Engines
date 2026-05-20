#!/usr/bin/env python3
"""
Process all Spider benchmark folders:
1. Convert SQLite databases to PostgreSQL SQL files
2. Normalize SQL queries for PostgreSQL compatibility
3. Delete CSV files

Usage: python scripts/process_all_spider.py [--dry-run]
"""

import sys
import subprocess
from pathlib import Path


def process_folder(folder_path: Path, dry_run: bool = False):
    """Process a single Spider folder"""
    folder_name = folder_path.name
    tables_dir = folder_path / "tables"
    
    # Check if tables directory exists
    if not tables_dir.exists():
        print(f"⚠️  Skipping {folder_name}: no tables/ directory")
        return False
    
    print(f"\n{'='*80}")
    print(f"Processing: {folder_name}")
    print(f"{'='*80}")
    
    # Step 1: Convert SQLite to PostgreSQL SQL
    print(f"\n[1/2] Converting SQLite to PostgreSQL SQL...")
    if not dry_run:
        try:
            result = subprocess.run(
                ["python", "scripts/sqlite_to_sql.py", str(tables_dir)],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            if result.stderr:
                print(f"  Warnings: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error converting database: {e}")
            print(f"  stdout: {e.stdout}")
            print(f"  stderr: {e.stderr}")
            return False
    else:
        print(f"  [DRY RUN] Would run: python scripts/sqlite_to_sql.py {tables_dir}")
    
    # Step 2: Normalize queries and delete CSVs
    print(f"\n[2/2] Normalizing queries and deleting CSVs...")
    if not dry_run:
        try:
            result = subprocess.run(
                ["python", "scripts/postgres_normalize.py", folder_name],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            if result.stderr:
                print(f"  Warnings: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error normalizing queries: {e}")
            print(f"  stdout: {e.stdout}")
            print(f"  stderr: {e.stderr}")
            return False
    else:
        print(f"  [DRY RUN] Would run: python scripts/postgres_normalize.py {folder_name}")
    
    print(f"✅ Completed: {folder_name}")
    return True


def main():
    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    # Find all Spider folders
    spider_dir = Path("benchmarks/spider")
    if not spider_dir.exists():
        print(f"❌ Error: {spider_dir} does not exist")
        sys.exit(1)
    
    # Get all subdirectories
    folders = sorted([f for f in spider_dir.iterdir() if f.is_dir()])
    
    print(f"Found {len(folders)} folders in {spider_dir}")
    
    # Process each folder
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for folder in folders:
        result = process_folder(folder, dry_run)
        if result is True:
            success_count += 1
        elif result is False:
            if folder.name in ["apartment_rentals"]:  # Already processed
                skip_count += 1
            else:
                error_count += 1
        else:
            skip_count += 1
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total folders: {len(folders)}")
    print(f"✅ Successfully processed: {success_count}")
    print(f"⚠️  Skipped: {skip_count}")
    print(f"❌ Errors: {error_count}")
    
    if dry_run:
        print(f"\n💡 This was a dry run. Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
