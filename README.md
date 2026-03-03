# CKAN Migrator

This repo helps with the migration of CKAN instances when you have a very old version of CKAN
and need to upgrade to a newer version.  

## Clean

Ensure cleaning previous data:

```bash
docker compose down -v
```

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
python -m pip install -r requirements.txt
```

### Analyze old data

Export all data from old database (do not migrate)

```bash
python migrate.py --mode extract
```

### Analyze old database structure

Export all db structure from old database (do not migrate)

```bash
python migrate.py --mode structure
```

### Analyze both old and new database structures

Export db structure from both databases for comparison (do not migrate)
Optional: Include new database parameters to also get the structure
of the new CKAN version database.  

```bash
python migrate.py --mode structure \
    --new-host localhost \
    --new-port 8012 \
    --new-dbname ckan_test \
    --new-user ckan_default \
    --new-password pass
```

#### Structure sample

You can see some database structure samples and diffs here:

 - [2.6.2 structure](/scripts/ckan_migrate/data-sample/database_report_2.6.2.md)
 - [2.11.3 structure](/scripts/ckan_migrate/data-sample/database_report_2.11.3.md)
 - [2.6.2 - 2.11.3 diff](/scripts/ckan_migrate/data-sample/diff-2.6.2-2.11.3.md)

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

### Move static files

```bash
rsync -av --progress /old-var/lib/ckan/ /new-var/lib/ckan/
```

## Production runbook (recommended order)

This section documents the exact sequence used successfully during migration.

### 0) Prerequisites

- Have the old DB dump available as `docker/dump/db.dump` (custom-format dump for `pg_restore`).
- Have old static files available in backup path:
    - `Back_up_original/var/lib/ckan/<instance>/storage/uploads`
    - `Back_up_original/var/lib/ckan/<instance>/resources`
- Ensure docker services are up (old postgres, new postgres, CKAN app, Solr, Redis).

### 1) Prepare Python environment (avoid system pip / PEP 668)

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements.txt
```

Verify:

```bash
which python
which pip
```

Both should point to this repo `.venv`.

### 2) Restore old DB into `postgres-old`

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml exec postgres-old \
    pg_restore --verbose --clean --if-exists --no-owner --no-acl \
    --dbname=old_ckan_db --username=postgres /dump/db.dump
```

Quick validation:

```bash
docker compose -f docker/docker-compose.yml exec postgres-old \
    psql -U postgres -d old_ckan_db -c "select count(*) from information_schema.tables where table_schema='public';"
```

### 3) Run migrator to target CKAN DB

```bash
cd scripts
python migrate.py --mode migrate \
    --new-host localhost \
    --new-port 8012 \
    --new-dbname ckan_test \
    --new-user ckan_default \
    --new-password pass
```

Optional checks:

```bash
python migrate.py --mode structure
python migrate.py --mode extract
```

### 4) Rebuild CKAN search index (required)

After migration, datasets may exist in DB but not be visible in UI until reindex.

Example (adapt container/config path to your deployment):

```bash
docker exec -i ckan_cba bash -lc \
    '/app/cba_gestionabierta/venv/bin/ckan -c /app/cba_gestionabierta/ckan.ini search-index rebuild -c -i'
```

Validate index count:

```bash
curl -s "http://localhost:5000/api/3/action/package_search?rows=0"
```

### 5) Restore static files (logos/images/uploads/resources)

This is mandatory to avoid 404 in organization/group logos and uploaded resources.

Copy `uploads`:

```bash
docker cp Back_up_original/var/lib/ckan/datosgestionabierta/storage/uploads/. \
    ckan_cba:/app/cba_gestionabierta/storage/storage/uploads/
docker exec -i ckan_cba bash -lc \
    'chown -R ckan:ckan /app/cba_gestionabierta/storage/storage/uploads'
```

Copy `resources`:

```bash
docker cp Back_up_original/var/lib/ckan/datosgestionabierta/resources/. \
    ckan_cba:/app/cba_gestionabierta/storage/resources/
docker exec -i ckan_cba bash -lc \
    'chown -R ckan:ckan /app/cba_gestionabierta/storage/resources'
```

### 6) Final validation checklist

- `/dataset` page shows datasets.
- Logos/images under `/uploads/group/...` return HTTP 200.
- Sample uploaded resource download works (not 404).
- `package_search` count is greater than zero.

### Notes

- If your dump is plain SQL (not custom-format), use `psql -f` instead of `pg_restore`.
- `migrate.py --mode all` is invalid; valid modes are: `migrate`, `structure`, `extract`.
- Replace container names (`ckan_cba`, `postgresql_cba`) and paths with your production equivalents.

## Backup validation (before migration)

To ensure your backup files are complete and match the production server, use these validation scripts:

### 0) Run full validation (master script)

Run all checks in one command (API counts, detailed dataset diffs, and SHA256 file-content comparison):

```bash
cd scripts
python run_full_validation.py \
  --remote-url https://datosgestionabierta.cba.gov.ar \
  --local-url http://localhost:5000 \
  --backup-base ../Back_up_original/var/lib/ckan/datosgestionabierta \
  --target-storage ../Back_up_original/var/lib/ckan/datosgestionabierta \
  --output full_validation_report_with_files.json
```

Notes:
- `--target-storage` should point to your restored CKAN storage (contains `resources` and `uploads` or `storage/uploads`).
- When `--target-storage` is set, file equality is checked by `SHA256` + relative path and reports missing/extra/different files.

### 1) Validate metadata via API (RECOMMENDED)

Compare CKAN API responses between your local backup and the production server:

```bash
cd scripts
python validate_backup.py \
  --remote-url https://datosgestionabierta.cba.gov.ar \
  --local-url http://localhost:5000
```

This will output:
- Package counts (local vs remote)
- Active packages comparison
- Total resources counts
- Sample dataset ID comparison
- Full JSON report in `backup_validation.json`

**Expected output on successful backup:**
```
Local Statistics:
  - Total packages:   145
  - Active packages:  145
  - Total resources:  953

Remote Statistics:
  - Total packages:   145
  - Active packages:  145
  - Total resources:  955

Differences Found: 1
  [resources] Local: 953, Remote: 955

Sample Dataset ID Comparison:
  - Matching IDs:     20
  - Local only:       0
  - Remote only:      0
```

**Why use API instead of direct DB:** Using the REST API validates that data is properly loaded into CKAN and accessible through the standard interface, which is how end-users will access it. It also eliminates the need for direct database credentials.

### 2) Deep package comparison

Compare actual package metadata (titles, resources, organizations):

```bash
python compare_remote_packages.py \
  --remote-url https://datosgestionabierta.cba.gov.ar \
  --sample-size 50
```

This fetches full metadata for 50 datasets and compares field-by-field.

### 3) Validate static files

Generate checksums for your local backup files:

```bash
./validate_files.sh Back_up_original/var/lib/ckan/datosgestionabierta
```

Output files:
- `file_validation/resources_checksums.txt` - MD5 checksums for all resource files
- `file_validation/uploads_checksums.txt` - MD5 checksums for all upload files

To compare with server:
1. Run the same script on the production server
2. Use `diff` to compare checksum files, or
3. Use `rsync --dry-run -avnc` to show differences without copying

**Recommended checks before migration:**
- Total package counts match exactly (same number of packages)
- Active packages match exactly
- Sample dataset IDs match 100% (critical indicator)
- Resource count difference < 2% (acceptable due to timing)
- File checksums match 100% (critical for data integrity)
