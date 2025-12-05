import logging


log = logging.getLogger(__name__)


def import_user_following_groups(old_user_following_groups, new_db, valid_users_ids=None):
    """ Get all old user following groups from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing user following groups...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    for user_following_group in old_user_following_groups:
        ret['total_rows'] += 1
        log.info(
            f"Importing user following group: {user_following_group['follower_id']} -> {user_following_group['object_id']}"
        )
        new_user_following_group = transform_user_following_group(user_following_group)
        if not new_user_following_group:
            log.warning(
                (
                    f" - Skipping user following group {user_following_group['follower_id']} -> "
                    f"{user_following_group['object_id']}."
                )
            )
            ret['skipped_rows'] += 1
            continue

        if valid_users_ids and new_user_following_group['follower_id'] not in valid_users_ids:
            ret['errors'].append(
                f" - User following group '{user_following_group['follower_id']} -> {user_following_group['object_id']}'"
                " ignored, the follower user does not exist in the new database."
            )
            ret['skipped_rows'] += 1
            continue

        fields = new_user_following_group.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the user following group relationship exists
        sql = 'SELECT * FROM "user_following_group" WHERE follower_id = %s AND object_id = %s'
        new_db.cursor.execute(sql, (user_following_group["follower_id"], user_following_group["object_id"]))
        if new_db.cursor.fetchone():
            log.warning(
                (
                    f" - User following group {user_following_group['follower_id']} -> "
                    "{user_following_group['object_id']} already exists, updating the record"
                )
            )
            sql = (
                f'UPDATE "user_following_group" SET ({", ".join(fields)}) = ({placeholders}) '
                'WHERE follower_id= %s AND object_id= %s'
            )
            new_db.cursor.execute(
                sql,
                tuple(
                    new_user_following_group[field]
                    for field in fields
                ) + (
                    user_following_group["follower_id"], user_following_group["object_id"]
                )
            )
        else:
            sql = f'INSERT INTO "user_following_group" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_user_following_group[field] for field in fields))
        log.info(
            (
                f" - User following group {user_following_group['follower_id']} -> "
                f"{user_following_group['object_id']} imported successfully."
            )
        )
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_user_following_group(user_following_group):
    """ Get an old db object and return a dict for the new DB object
        Old user following groups looks like:
          {
            "follower_id":"user-id",
            "object_id":"group-id",
            "datetime":"2017-03-21 18:23:56.055936"
        },
    """
    new_user_following_group = {
        'follower_id': user_following_group['follower_id'],
        'object_id': user_following_group['object_id'],
        'datetime': user_following_group['datetime']
    }

    return new_user_following_group
