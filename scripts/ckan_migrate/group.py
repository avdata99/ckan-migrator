import logging


log = logging.getLogger(__name__)


def import_groups(old_groups, new_db):
    """ Get all old groups from CSV and import them """
    log.info("Importing groups...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': [],
        'valid_groups_ids': []  # Initialize valid_groups_ids here
    }
    names_in_use = []
    for group in old_groups:
        ret['total_rows'] += 1
        log.info(f"Importing group: {group['name']}")
        new_group = transform_group(group)
        if not new_group:
            log.warning(f" - Skipping group {group['name']}.")
            ret['skipped_rows'] += 1
            continue

        if new_group['name'] in names_in_use:
            # Add a suffix to the name
            original_name = new_group['name']
            new_group['name'] = f"{original_name}_{hash(group['id'])}"
            ret['errors'].append(
                f" - Group '{original_name}' has a duplicate name."
                f" New name: {new_group['name']} (old: {original_name})"
            )
        ret['valid_groups_ids'].append(new_group['id'])

        fields = new_group.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the group ID exists
        sql = 'SELECT * FROM "group" WHERE id = %s'
        new_db.cursor.execute(sql, (group["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Group {group['name']} already exists, updating the record")
            sql = f'UPDATE "group" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_group[field] for field in fields) + (group["id"],))
        else:
            sql = f'INSERT INTO "group" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_group[field] for field in fields))
        log.info(f" - Group {group['name']} imported successfully.")
        names_in_use.append(new_group['name'])
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_group(group, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old groups looks like:
          {
            "id":"group-id",
            "name":"group-name",
            "title":"Group Title",
            "description":"Group description",
            "created":"2017-03-21 18:23:56.055936",
            "state":"active",
            "revision_id":"revision-id",
            "type":"group",
            "approval_status":"approved",
            "image_url":"http://example.com/image.png",
            "is_organization":false
        },
    """
    if not migrate_deleted and group['state'] == 'deleted':
        return None

    new_group = {
        'id': group['id'],
        'name': group['name'],
        'title': group['title'],
        'description': group['description'],
        'created': group['created'],
        'state': group['state'],
        'type': group['type'],
        'approval_status': group['approval_status'],
        'image_url': group['image_url'],
        'is_organization': group['is_organization']
    }

    return new_group
