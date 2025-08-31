import logging


log = logging.getLogger(__name__)


def import_resource_views(old_db, new_db):
    """ Get all old resource views from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting resource views from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "resource_view" ORDER BY "order"'
    old_db.cursor.execute(query)
    resource_views = old_db.cursor.fetchall()

    for resource_view in resource_views:
        ret['total_rows'] += 1
        log.info(f"Importing resource view: {resource_view['id']} (type: {resource_view['view_type']})")
        new_resource_view = transform_resource_view(resource_view)
        if not new_resource_view:
            log.warning(f" - Skipping resource view {resource_view['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_resource_view.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the resource view ID exists
        sql = 'SELECT * FROM "resource_view" WHERE id = %s'
        new_db.cursor.execute(sql, (resource_view["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Resource view {resource_view['id']} already exists, updating the record")
            sql = f'UPDATE "resource_view" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_resource_view[field] for field in fields) + (resource_view["id"],))
        else:
            sql = f'INSERT INTO "resource_view" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_resource_view[field] for field in fields))
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
