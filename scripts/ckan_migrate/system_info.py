import logging


log = logging.getLogger(__name__)


def import_system_info(old_db, new_db):
    """ Get all old system info from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting system info from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "system_info" ORDER BY id'
    old_db.cursor.execute(query)
    system_infos = old_db.cursor.fetchall()

    for system_info in system_infos:
        ret['total_rows'] += 1
        log.info(f"Importing system info: {system_info['key']}")
        new_system_info = transform_system_info(system_info)
        if not new_system_info:
            log.warning(f" - Skipping system info {system_info['key']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_system_info.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the system info ID exists
        sql = 'SELECT * FROM "system_info" WHERE id = %s'
        new_db.cursor.execute(sql, (system_info["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - System info {system_info['key']} already exists, updating the record")
            sql = f'UPDATE "system_info" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_system_info[field] for field in fields) + (system_info["id"],))
        else:
            sql = f'INSERT INTO "system_info" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_system_info[field] for field in fields))
        log.info(f" - System info {system_info['key']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_system_info(system_info, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old system info looks like:
          {
            "id":1,
            "key":"site_title",
            "value":"CKAN Demo",
            "revision_id":"revision-id",  # DEPRECATED - removed in new CKAN
            "state":"active"
        },
    """
    if not migrate_deleted and system_info['state'] == 'deleted':
        return None

    new_system_info = {
        'id': system_info['id'],
        'key': system_info['key'],
        'value': system_info['value'],
        'state': system_info['state']
    }

    # Note: revision_id is deprecated in new CKAN - we skip it

    return new_system_info
