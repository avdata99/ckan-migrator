import logging


log = logging.getLogger(__name__)


def import_revisions(old_db, new_db):
    """ Get all old revisions from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting revisions from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "revision" ORDER BY timestamp'
    old_db.cursor.execute(query)
    revisions = old_db.cursor.fetchall()

    for revision in revisions:
        ret['total_rows'] += 1
        log.info(f"Importing revision: {revision['id']}")
        new_revision = transform_revision(revision)
        if not new_revision:
            log.warning(f" - Skipping revision {revision['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_revision.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the revision ID exists
        sql = 'SELECT * FROM "revision" WHERE id = %s'
        new_db.cursor.execute(sql, (revision["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Revision {revision['id']} already exists, updating the record")
            sql = f'UPDATE "revision" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_revision[field] for field in fields) + (revision["id"],))
        else:
            sql = f'INSERT INTO "revision" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_revision[field] for field in fields))
        log.info(f" - Revision {revision['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_revision(revision):
    """ Get an old db object and return a dict for the new DB object
        Old revisions looks like:
          {
            "id":"revision-id",
            "timestamp":"2017-03-21 18:23:56.055936",
            "author":"author-name",
            "message":"Revision message",
            "state":"active",
            "approved_timestamp":"2017-03-21 18:23:56.055936"
        },
    """
    new_revision = {
        'id': revision['id'],
        'timestamp': revision['timestamp'],
        'author': revision['author'],
        'message': revision['message'],
        'state': revision['state'],
        'approved_timestamp': revision['approved_timestamp']
    }

    return new_revision
