import logging


log = logging.getLogger(__name__)


def import_activities(old_activities, new_db, valid_users_ids=None):
    """ Get all old activities from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing activities...")
    ret = {
        'valid_activities_ids': [],
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    for activity in old_activities:
        ret['total_rows'] += 1
        log.info(f"Importing activity: {activity['id']} (type: {activity['activity_type']})")
        new_activity = transform_activity(activity)
        if not new_activity:
            log.warning(f" - Skipping activity {activity['id']}.")
            ret['skipped_rows'] += 1
            continue

        if valid_users_ids and new_activity['user_id'] and new_activity['user_id'] not in valid_users_ids:
            ret['skipped_rows'] += 1
            continue

        ret['valid_activities_ids'].append(new_activity['id'])
        fields = new_activity.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the activity ID exists
        sql = 'SELECT * FROM "activity" WHERE id = %s'
        new_db.cursor.execute(sql, (activity["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Activity {activity['id']} already exists, updating the record")
            sql = f'UPDATE "activity" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            try:
                new_db.cursor.execute(sql, tuple(new_activity[field] for field in fields) + (activity["id"],))
            except Exception as e:
                log.error(f" - Error updating activity {activity['id']}: {e}")
                ret['errors'].append(f"Error updating activity {activity['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        else:
            sql = f'INSERT INTO "activity" ({", ".join(fields)}) VALUES ({placeholders})'
            try:
                new_db.cursor.execute(sql, tuple(new_activity[field] for field in fields))
            except Exception as e:
                log.error(f" - Error inserting activity {activity['id']}: {e}")
                ret['errors'].append(f"Error inserting activity {activity['id']}: {e}")
                ret['skipped_rows'] += 1
                # rollback to keep the transaction clean
                new_db.conn.rollback()
                continue
        log.info(f" - Activity {activity['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_activity(activity):
    """ Get an old db object and return a dict for the new DB object
        Old activities looks like:
          {
            "id":"activity-id",
            "timestamp":"2017-03-21 18:23:56.055936",
            "user_id":"user-id",
            "object_id":"object-id",
            "revision_id":"revision-id",
            "activity_type":"new package",
            "data":"{\"package\": {...}}"
        },
        New activities add:
          - "permission_labels": [] (new field in CKAN 2.11)
    """
    new_activity = {
        'id': activity['id'],
        'timestamp': activity['timestamp'],
        'user_id': activity['user_id'],
        'object_id': activity['object_id'],
        'revision_id': activity['revision_id'],
        'activity_type': activity['activity_type'],
        'data': activity['data'],
        'permission_labels': ['public']  # New field - set to public for migrated activities
    }

    return new_activity
