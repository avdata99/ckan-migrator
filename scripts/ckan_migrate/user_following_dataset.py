import logging


log = logging.getLogger(__name__)


def import_user_following_datasets(old_db, new_db):
    """ Get all old user following datasets from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting user following datasets from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "user_following_dataset" ORDER BY datetime'
    old_db.cursor.execute(query)
    user_following_datasets = old_db.cursor.fetchall()

    for user_following_dataset in user_following_datasets:
        ret['total_rows'] += 1
        log.info(
            f"Importing user fo.ing dataset: {user_following_dataset['follower_id']} -> {user_following_dataset['object_id']}"
        )
        new_user_following_dataset = transform_user_following_dataset(user_following_dataset)
        if not new_user_following_dataset:
            log.warning(
                (
                    f" - Skipping user following dataset {user_following_dataset['follower_id']} -> "
                    f"{user_following_dataset['object_id']}."
                )
            )
            ret['skipped_rows'] += 1
            continue

        fields = new_user_following_dataset.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the user following dataset relationship exists
        sql = 'SELECT * FROM "user_following_dataset" WHERE follower_id = %s AND object_id = %s'
        new_db.cursor.execute(sql, (user_following_dataset["follower_id"], user_following_dataset["object_id"]))
        if new_db.cursor.fetchone():
            log.warning(
                (
                    f" - User following dataset {user_following_dataset['follower_id']} -> "
                    f"{user_following_dataset['object_id']} already exists, updating the record"
                )
            )
            sql = (
                f'UPDATE "user_following_dataset" SET ({", ".join(fields)}) = ({placeholders}) '
                'WHERE follower_id= %s AND object_id= %s'
            )
            new_db.cursor.execute(
                sql,
                tuple(
                    new_user_following_dataset[field] for field in fields
                ) + (
                    user_following_dataset["follower_id"], user_following_dataset["object_id"]
                )
            )
        else:
            sql = f'INSERT INTO "user_following_dataset" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_user_following_dataset[field] for field in fields))
        log.info(
            (
                f" - User following dataset {user_following_dataset['follower_id']} -> "
                f"{user_following_dataset['object_id']} imported successfully."
            )
        )
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_user_following_dataset(user_following_dataset):
    """ Get an old db object and return a dict for the new DB object
        Old user following datasets looks like:
          {
            "follower_id":"user-id",
            "object_id":"dataset-id",
            "datetime":"2017-03-21 18:23:56.055936"
        },
    """
    new_user_following_dataset = {
        'follower_id': user_following_dataset['follower_id'],
        'object_id': user_following_dataset['object_id'],
        'datetime': user_following_dataset['datetime']
    }

    return new_user_following_dataset
