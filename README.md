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

