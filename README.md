# CKAN Migrator

This repo helps with the migration of CKAN instances when you have a very old version of CKAN
and need to upgrade to a newer version.  

## Import old DB

Move you CKAN DB dump to `docker/dump/db.dump`.  

Start the container with `docker compose up`.  

Then, restore the database using:

```bash
docker compose exec postgres-old \
    pg_restore --verbose --clean \
    --if-exists --no-owner --no-acl \
    --dbname=old_ckan_db \
    --username=postgres \
    /dump/db.dump
```

## Run the migration script

Install the required dependencies

```bash
cd scripts
pip install -r requirements.txt
```

### Analyze old data

Export all data from old database (do not migrate)

```bash
python migrate.py --mode all
```

### Analyze old database structure

Export all db structure from old database (do not migrate)

```bash
python migrate.py --mode structure
```

### Output Files

The script generates several output files:

1. **`database_report.md`** - Comprehensive markdown report with:
   - Database overview
   - Table summaries (name, row count, column count)
   - Detailed column information for each table
   - Summary statistics

2. **`tables_info.json`** - JSON file with detailed table metadata:
   - Column names, types, nullability, defaults
   - Row counts for each table

3. **`extracted_data/` directory** (if data extraction is enabled):
   - `{table_name}.csv` - CSV files for each table
   - `{table_name}.json` - JSON files for each table

### Full migration

```bash
python migrate.py --mode migrate \
    --new-host localhost \
    --new-port 8012 \
    --new-dbname ckan_test \
    --new-user ckan_default \
    --new-password pass
```
