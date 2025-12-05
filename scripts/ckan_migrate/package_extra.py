import logging


log = logging.getLogger(__name__)


def import_package_extras(old_package_extras, new_db):
    """ Get all old package extras from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing package extras...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    for package_extra in old_package_extras:
        ret['total_rows'] += 1
        log.info(f"Importing package extra: {package_extra['id']} (key: {package_extra['key']})")
        new_package_extra = transform_package_extra(package_extra)
        if not new_package_extra:
            log.warning(f" - Skipping package extra {package_extra['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_package_extra.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the package extra ID exists
        sql = 'SELECT * FROM "package_extra" WHERE id = %s'
        new_db.cursor.execute(sql, (package_extra["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Package extra {package_extra['id']} already exists, updating the record")
            sql = f'UPDATE "package_extra" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            try:
                new_db.cursor.execute(sql, tuple(new_package_extra[field] for field in fields) + (package_extra["id"],))
            except Exception as e:
                log.error(f" - Error updating package extra {package_extra['id']}: {e}")
                ret['errors'].append(f"Error updating package extra {package_extra['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        else:
            sql = f'INSERT INTO "package_extra" ({', '.join(fields)}) VALUES ({placeholders})'
            try:
                new_db.cursor.execute(sql, tuple(new_package_extra[field] for field in fields))
            except Exception as e:
                log.error(f" - Error inserting package extra {package_extra['id']}: {e}")
                ret['errors'].append(f"Error inserting package extra {package_extra['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        log.info(f" - Package extra {package_extra['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_package_extra(package_extra, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old package extras looks like:
          {
            "id":"package-extra-id",
            "package_id":"package-id",
            "key":"metadata_key",
            "value":"metadata_value",
            "revision_id":"revision-id",  # DEPRECATED - removed in new CKAN
            "state":"active"
        },
    """
    if not migrate_deleted and package_extra['state'] == 'deleted':
        return None

    new_package_extra = {
        'id': package_extra['id'],
        'package_id': package_extra['package_id'],
        'key': package_extra['key'],
        'value': package_extra['value'],
        'state': package_extra['state']
    }

    # Note: revision_id is deprecated in new CKAN - we skip it

    return new_package_extra
