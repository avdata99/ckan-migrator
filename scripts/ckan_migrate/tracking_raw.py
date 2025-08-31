import logging


log = logging.getLogger(__name__)


def import_tracking_raw(old_db, new_db):
    """ Get all old tracking raw from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting tracking raw from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "tracking_raw" ORDER BY access_timestamp'
    old_db.cursor.execute(query)
    tracking_raws = old_db.cursor.fetchall()

    for tracking_raw in tracking_raws:
        ret['total_rows'] += 1
        log.info(f"Importing tracking raw: {tracking_raw['user_key']} ({tracking_raw['tracking_type']})")
        new_tracking_raw = transform_tracking_raw(tracking_raw)
        if not new_tracking_raw:
            log.warning(f" - Skipping tracking raw {tracking_raw['user_key']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_tracking_raw.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the tracking raw exists (composite primary key)
        sql = ('SELECT * FROM "tracking_raw" WHERE user_key = %s AND url = %s '
               'AND tracking_type = %s AND access_timestamp = %s')
        new_db.cursor.execute(
            sql, (
                tracking_raw["user_key"], tracking_raw["url"],
                tracking_raw["tracking_type"], tracking_raw["access_timestamp"]
            )
        )
        if new_db.cursor.fetchone():
            log.warning(f" - Tracking raw {tracking_raw['user_key']} already exists, skipping")
            ret['skipped_rows'] += 1
            continue
        else:
            sql = f'INSERT INTO "tracking_raw" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_tracking_raw[field] for field in fields))
        log.info(f" - Tracking raw {tracking_raw['user_key']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_tracking_raw(tracking_raw):
    """ Get an old db object and return a dict for the new DB object
        Old tracking raw looks like:
          {
            "user_key":"user-key-123",
            "url":"http://example.com/dataset/test",
            "tracking_type":"page",
            "access_timestamp":"2017-03-21 18:23:56.055936"
        },
    """
    new_tracking_raw = {
        'user_key': tracking_raw['user_key'],
        'url': tracking_raw['url'],
        'tracking_type': tracking_raw['tracking_type'],
        'access_timestamp': tracking_raw['access_timestamp']
    }

    return new_tracking_raw
