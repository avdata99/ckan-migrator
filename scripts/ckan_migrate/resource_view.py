import logging


log = logging.getLogger(__name__)


def import_resource_views(old_resource_views, new_db):
    """ Get all old resource views from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing resource views...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    for resource_view in old_resource_views:
        ret['total_rows'] += 1
        log.info(f"Importing resource view: {resource_view['id']} (type: {resource_view['view_type']})")
        new_resource_view = transform_resource_view(resource_view)
        if not new_resource_view:
            log.warning(f" - Skipping resource view {resource_view['id']}.")
            ret['skipped_rows'] += 1
            continue

        # Quote field names to handle reserved keywords like 'order'
        quoted_fields = [f'"{field}"' for field in new_resource_view.keys()]
        placeholders = ', '.join(['%s'] * len(quoted_fields))
        # Check if the resource view ID exists
        sql = 'SELECT * FROM "resource_view" WHERE id = %s'
        new_db.cursor.execute(sql, (resource_view["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Resource view {resource_view['id']} already exists, updating the record")
            sql = f'UPDATE "resource_view" SET ({", ".join(quoted_fields)}) = ({placeholders}) WHERE id= %s'
            try:
                new_db.cursor.execute(
                    sql,
                    tuple(new_resource_view[field.strip('"')] for field in quoted_fields) + (resource_view["id"],)
                )
            except Exception as e:
                log.error(f" - Error updating resource view {resource_view['id']}: {e}")
                ret['errors'].append(f"Error updating resource view {resource_view['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        else:
            sql = f'INSERT INTO "resource_view" ({", ".join(quoted_fields)}) VALUES ({placeholders})'
            try:
                new_db.cursor.execute(sql, tuple(new_resource_view[field.strip('"')] for field in quoted_fields))
            except Exception as e:
                log.error(f" - Error inserting resource view {resource_view['id']}: {e}")
                ret['errors'].append(f"Error inserting resource view {resource_view['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        log.info(f" - Resource view {resource_view['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_resource_view(resource_view):
    """ Get an old db object and return a dict for the new DB object
        Old resource views looks like:
          {
            "id":"resource-view-id",
            "resource_id":"resource-id",
            "title":"View Title",
            "description":"View description",
            "view_type":"chart",
            "order":0,
            "config":"{\"chart_type\":\"bar\"}"
        },
    """
    new_resource_view = {
        'id': resource_view['id'],
        'resource_id': resource_view['resource_id'],
        'title': resource_view['title'],
        'description': resource_view['description'],
        'view_type': resource_view['view_type'],
        'order': resource_view['order'],
        'config': resource_view['config']
    }

    return new_resource_view
