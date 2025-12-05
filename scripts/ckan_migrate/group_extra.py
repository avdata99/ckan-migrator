import logging


log = logging.getLogger(__name__)


def import_group_extras(old_group_extras, new_db):
    """ Get all old group extras from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing group extras...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    for group_extra in old_group_extras:
        ret['total_rows'] += 1
        log.info(f"Importing group extra: {group_extra['id']} (key: {group_extra['key']})")
        new_group_extra = transform_group_extra(group_extra)
        if not new_group_extra:
            log.warning(f" - Skipping group extra {group_extra['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_group_extra.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the group extra ID exists
        sql = 'SELECT * FROM "group_extra" WHERE id = %s'
        new_db.cursor.execute(sql, (group_extra["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Group extra {group_extra['id']} already exists, updating the record")
            sql = f'UPDATE "group_extra" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_group_extra[field] for field in fields) + (group_extra["id"],))
        else:
            sql = f'INSERT INTO "group_extra" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_group_extra[field] for field in fields))
        log.info(f" - Group extra {group_extra['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_group_extra(group_extra, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old group extras looks like:
          {
            "id":"group-extra-id",
            "group_id":"group-id",
            "key":"metadata_key",
            "value":"metadata_value",
            "state":"active",
            "revision_id":"revision-id"  # DEPRECATED - removed in new CKAN
        },
    """
    if not migrate_deleted and group_extra['state'] == 'deleted':
        return None

    new_group_extra = {
        'id': group_extra['id'],
        'group_id': group_extra['group_id'],
        'key': group_extra['key'],
        'value': group_extra['value'],
        'state': group_extra['state']
    }

    # Note: revision_id is deprecated in new CKAN - we skip it

    return new_group_extra
