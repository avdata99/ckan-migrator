import logging


log = logging.getLogger(__name__)


def import_members(old_db, new_db, valid_users_ids=None):
    """ Get all old members from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting members from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "member"'
    old_db.cursor.execute(query)
    members = old_db.cursor.fetchall()

    for member in members:
        ret['total_rows'] += 1
        log.info(f"Importing member: {member['id']} (table: {member['table_name']}, capacity: {member['capacity']})")
        new_member = transform_member(member)
        if not new_member:
            log.warning(f" - Skipping member {member['id']}.")
            ret['skipped_rows'] += 1
            continue

        # if table is "user", check if the user_id exists in the new DB
        if member['table_name'] == 'user' and valid_users_ids and member['table_id'] not in valid_users_ids:
            ret['errors'].append(
                f" - Member '{member['id']}' ignored, has a table_id '{member['table_id']}'"
                " that does not exist in the new database. Setting it to None."
            )
            ret['skipped_rows'] += 1
            continue

        fields = new_member.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the member ID exists
        sql = 'SELECT * FROM "member" WHERE id = %s'
        new_db.cursor.execute(sql, (member["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Member {member['id']} already exists, updating the record")
            sql = f'UPDATE "member" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_member[field] for field in fields) + (member["id"],))
        else:
            sql = f'INSERT INTO "member" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_member[field] for field in fields))
        log.info(f" - Member {member['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_member(member, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old members looks like:
          {
            "id":"member-id",
            "table_id":"package-id or user-id",
            "group_id":"group-id",
            "state":"active",
            "revision_id":"revision-id",  # DEPRECATED - removed in new CKAN
            "table_name":"package or user",
            "capacity":"member or admin or editor"
        },
    """
    if not migrate_deleted and member['state'] == 'deleted':
        return None

    new_member = {
        'id': member['id'],
        'table_id': member['table_id'],
        'group_id': member['group_id'],
        'state': member['state'],
        'table_name': member['table_name'],
        'capacity': member['capacity']
    }

    # Note: revision_id is deprecated in new CKAN - we skip it

    return new_member
