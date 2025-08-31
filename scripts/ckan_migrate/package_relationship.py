import logging


log = logging.getLogger(__name__)


def import_package_relationships(old_db, new_db):
    """ Get all old package relationships from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting package relationships from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "package_relationship"'
    old_db.cursor.execute(query)
    package_relationships = old_db.cursor.fetchall()

    for package_relationship in package_relationships:
        ret['total_rows'] += 1
        log.info(f"Importing package relationship: {package_relationship['id']} ({package_relationship['type']})")
        new_package_relationship = transform_package_relationship(package_relationship)
        if not new_package_relationship:
            log.warning(f" - Skipping package relationship {package_relationship['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_package_relationship.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the package relationship ID exists
        sql = 'SELECT * FROM "package_relationship" WHERE id = %s'
        new_db.cursor.execute(sql, (package_relationship["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Package relationship {package_relationship['id']} already exists, updating the record")
            sql = f'UPDATE "package_relationship" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(
                sql, tuple(new_package_relationship[field] for field in fields) + (package_relationship["id"],)
            )
        else:
            sql = f'INSERT INTO "package_relationship" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_package_relationship[field] for field in fields))
        log.info(f" - Package relationship {package_relationship['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_package_relationship(package_relationship, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old package relationships looks like:
          {
            "id":"package-relationship-id",
            "subject_package_id":"package-id",
            "object_package_id":"package-id",
            "type":"depends_on",
            "comment":"Relationship comment",
            "revision_id":"revision-id",  # DEPRECATED - removed in new CKAN
            "state":"active"
        },
    """
    if not migrate_deleted and package_relationship['state'] == 'deleted':
        return None

    new_package_relationship = {
        'id': package_relationship['id'],
        'subject_package_id': package_relationship['subject_package_id'],
        'object_package_id': package_relationship['object_package_id'],
        'type': package_relationship['type'],
        'comment': package_relationship['comment'],
        'state': package_relationship['state']
    }

    # Note: revision_id is deprecated in new CKAN - we skip it

    return new_package_relationship
