# CKAN Migrator (EN)

Tool to migrate **old CKAN instances** to newer versions, allowing you to extract and transfer data from an old PostgreSQL database to a newer one.  

Includes:
- Full export of data and structure (CSV/JSON).
- Migration of key entities (`users`, `organizations`, `groups`).
- Support to extend migration to more tables (`tags`, `packages`, `resources`, etc.).

## 📦 Preparation

### 1. Import the old database

Place your dump in:

```
docker/dump/db.dump
```

Start the containers:

```bash
cd docker
docker compose up -d
```

Restore the dump into `postgres-old`:

```bash
docker compose exec postgres-old     pg_restore --verbose --clean     --if-exists --no-owner --no-acl     --dbname=old_ckan_db     --username=postgres     /dump/db.dump
```

This sets up the **`old_ckan_db`** DB on port `9133`.

---

### 2. Configure the migration environment

```bash
cd scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Main dependencies:
- `psycopg2-binary`
- `pandas`
- `numpy`

---

## ⚙️ Usage modes

### 1. Export all old CKAN data (read-only)

```bash
python migrate.py --mode all
```

Generates:

- **`database_report.md`** → Full report of tables, rows, and columns.
- **`tables_info.json`** → Structural metadata of all tables.
- **`extracted_data/`** → CSV + JSON for each table.

---

### 2. Export only the structure (no data)

```bash
python migrate.py --mode structure
```

---

### 3. Migrate to a new CKAN database

Example with a new CKAN running on port **8012**:

```bash
python migrate.py --mode migrate   --new-host localhost   --new-port 8012   --new-dbname ckan_test   --new-user ckan_default   --new-password pass
```

---

## 🔀 Migration steps

The `--steps` parameter defines which entities to migrate.  
Default: `users,organizations,groups`

### Migrate users

```bash
python migrate.py --mode migrate --steps users ...
```

### Migrate organizations

```bash
python migrate.py --mode migrate --steps organizations ...
```

### Migrate groups

```bash
python migrate.py --mode migrate --steps groups ...
```

### Migrate multiple steps

```bash
python migrate.py --mode migrate --steps users,organizations,groups ...
```

---

## 🧩 Extending with new modules

Each entity migration is implemented in a file inside `scripts/ckan_migrate/`.  
Current examples:
- `user.py` → users migration
- `organization.py` → organizations migration
- `groups.py` → groups migration

To add new tables (e.g. `tags`):
1. Create `tags.py` in `scripts/ckan_migrate/`.
2. Implement `import_tags(old_db, new_db)`.
3. Import it in `migrate.py` and enable in `--steps`.

---

## 📝 Important notes

- Some corrupted dates in old databases may trigger pandas warnings (`Overflow in npy_datetimestruct_to_datetime`). The script handles them and generates a *fallback* JSON.
- Migration is intended for CKAN ≥2.11 as the target.
- It is recommended to run `--mode all` first to inspect exported data.

---

## ✅ Current status

- Full export working.
- Partial migration (`users`, `organizations`, `groups`) implemented.
- Ready to extend to `tags`, `packages`, `resources`.
