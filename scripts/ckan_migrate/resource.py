import logging


log = logging.getLogger(__name__)


def import_resources(old_db, new_db):
    """ Get all old resources from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting resources from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "resource" ORDER BY created'
    old_db.cursor.execute(query)
    resources = old_db.cursor.fetchall()

    for resource in resources:
        ret['total_rows'] += 1
        log.info(f"Importing resource: {resource['id']}")
        new_resource = transform_resource(resource)
        if not new_resource:
            log.warning(f" - Skipping resource {resource['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_resource.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the resource ID exists
        sql = 'SELECT * FROM "resource" WHERE id = %s'
        new_db.cursor.execute(sql, (resource["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Resource {resource['id']} already exists, updating the record")
            sql = f'UPDATE "resource" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            try:
                new_db.cursor.execute(sql, tuple(new_resource[field] for field in fields) + (resource["id"],))
            except Exception as e:
                log.error(f" - Error updating resource {resource['id']}: {e}")
                ret['errors'].append(f"Error updating resource {resource['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        else:
            sql = f'INSERT INTO "resource" ({', '.join(fields)}) VALUES ({placeholders})'
            try:
                new_db.cursor.execute(sql, tuple(new_resource[field] for field in fields))
            except Exception as e:
                log.error(f" - Error inserting resource {resource['id']}: {e}")
                ret['errors'].append(f"Error inserting resource {resource['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        log.info(f" - Resource {resource['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_resource(resource, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old resources looks like:
          {
            "id":"resource-id",
            "url":"http://example.com/resource.csv",
            "format":"CSV",
            "description":"Resource description",
            "position":0,
            "revision_id":"revision-id",  # DEPRECATED - removed in new CKAN
            "hash":"md5hash",
            "state":"active",
            "extras":"{}",
            "name":"Resource Name",
            "resource_type":"file",
            "mimetype":"text/csv",
            "mimetype_inner":"text/csv",
            "size":1024,
            "last_modified":"2017-03-21 18:23:56.055936",
            "cache_url":"http://cache.example.com/resource.csv",
            "cache_last_updated":"2017-03-21 18:23:56.055936",
            "webstore_url":"http://webstore.example.com",  # DEPRECATED - removed in new CKAN
            "webstore_last_updated":"2017-03-21 18:23:56.055936",  # DEPRECATED - removed in new CKAN
            "created":"2017-03-21 18:23:56.055936",
            "url_type":"upload",
            "package_id":"package-id"
        },
    """
    if not migrate_deleted and resource['state'] == 'deleted':
        return None

    new_resource = {
        'id': resource['id'],
        'url': resource['url'],
        'format': resource['format'],
        'description': resource['description'],
        'position': resource['position'],
        'hash': resource['hash'],
        'state': resource['state'],
        'extras': resource['extras'],
        'name': resource['name'],
        'resource_type': resource['resource_type'],
        'mimetype': resource['mimetype'],
        'mimetype_inner': resource['mimetype_inner'],
        'size': resource['size'],
        'last_modified': resource['last_modified'],
        'cache_url': resource['cache_url'],
        'cache_last_updated': resource['cache_last_updated'],
        'created': resource['created'],
        'url_type': resource['url_type'],
        'package_id': resource['package_id']
    }

    # Add metadata_modified field (new in CKAN 2.11) - use created date as fallback
    new_resource['metadata_modified'] = resource.get('metadata_modified', resource['created'])

    # Note: revision_id, webstore_url, webstore_last_updated are deprecated in new CKAN - we skip them

    return new_resource
