import logging


log = logging.getLogger(__name__)


def import_users(old_db, new_db):
    """ Get all old users from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting users from old database...")
    ret = {
        'valid_users_ids': [],
        'valid_users_names': [],
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "user"'
    old_db.cursor.execute(query)
    users = old_db.cursor.fetchall()
    # Old CKAN version allows duplicated emails
    # CKAN 2.11 do not allow them so we will hack them
    emails_in_use = []
    for user in users:
        ret['total_rows'] += 1
        log.info(f"Importing user: {user['name']}")
        new_user = transform_user(user)
        if not new_user:
            log.warning(f" - Skipping user {user['name']}.")
            ret['skipped_rows'] += 1
            continue

        ret['valid_users_ids'].append(new_user['id'])
        ret['valid_users_names'].append(new_user['name'])
        if new_user['email'] and new_user['email'] in emails_in_use:
            # Add a hash to the email
            dup_email = new_user['email']
            parts = new_user['email'].split('@')
            new_user['email'] = f"{parts[0]}_{hash(user['id'])}@{parts[1]}"
            ret['errors'].append(
                f" - User '{user['name']}' has a duplicate email."
                f" New email: {new_user['email']} (old: {dup_email})"
            )

        fields = new_user.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the user ID exists
        sql = 'SELECT * FROM "user" WHERE id = %s'
        new_db.cursor.execute(sql, (user["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - User {user['name']} already exists, updating the record")
            sql = f'UPDATE "user" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_user[field] for field in fields) + (user["id"],))
        else:
            sql = f'INSERT INTO "user" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_user[field] for field in fields))
        log.info(f" - User {user['name']} imported successfully.")
        emails_in_use.append(new_user['email'])
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_user(user, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old users looks like (it could be different in your case)
          {
            "id":"0478ad7d-xxxxx",
            "name":"some-user-5802",
            "apikey":"d66....",
            "created":"2017-03-21 18:23:56.055936",
            "about":null,
            "password":"$pbkdf2-....",
            "fullname":null,
            "email":"someuser@gmail.com.ar",
            "reset_key":"5c4....",
            "sysadmin":false,
            "activity_streams_email_notifications":false,
            "state":"deleted"
        },
    """
    if not migrate_deleted and user['state'] == 'deleted':
        return None

    new_user = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'about': user['about'],
        'created': user['created'],
        'fullname': user['fullname'],
        'sysadmin': user['sysadmin'],
        'state': user['state']
    }

    return new_user
