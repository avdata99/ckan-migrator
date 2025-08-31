import logging


log = logging.getLogger(__name__)


def import_package_tags(old_db, new_db):
    """ Get all old package tags from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting package tags from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "package_tag"'
    old_db.cursor.execute(query)
    package_tags = old_db.cursor.fetchall()

    for package_tag in package_tags:
        ret['total_rows'] += 1
        log.info(
            f"Importing package tag: {package_tag['id']} (package: {package_tag['package_id']}, tag: {package_tag['tag_id']})"
        )
        new_package_tag = transform_package_tag(package_tag)
        if not new_package_tag:
            log.warning(f" - Skipping package tag {package_tag['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_package_tag.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the package tag ID exists
        sql = 'SELECT * FROM "package_tag" WHERE id = %s'
        new_db.cursor.execute(sql, (package_tag["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Package tag {package_tag['id']} already exists, updating the record")
            sql = f'UPDATE "package_tag" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_package_tag[field] for field in fields) + (package_tag["id"],))
        else:
            sql = f'INSERT INTO "package_tag" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_package_tag[field] for field in fields))
        log.info(f" - Package tag {package_tag['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_package_tag(package_tag, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old package tags looks like:
          {
            "id":"package-tag-id",
            "package_id":"package-id",
            "tag_id":"tag-id",
            "revision_id":"revision-id",  # DEPRECATED - removed in new CKAN
            "state":"active"
        },
    """
    if not migrate_deleted and package_tag['state'] == 'deleted':
        return None

    new_package_tag = {
        'id': package_tag['id'],
        'package_id': package_tag['package_id'],
        'tag_id': package_tag['tag_id'],
        'state': package_tag['state']
    }

    # Note: revision_id is deprecated in new CKAN - we skip it

    return new_package_tag
