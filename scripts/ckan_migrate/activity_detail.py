import logging


log = logging.getLogger(__name__)


def import_activity_details(old_activity_details, new_db, valid_activities_ids=None):
    """ Get all old activity details from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing activity details...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    for activity_detail in old_activity_details:
        ret['total_rows'] += 1
        log.info(f"Importing activity detail: {activity_detail['id']} (activity: {activity_detail['activity_id']})")
        new_activity_detail = transform_activity_detail(activity_detail)
        if not new_activity_detail:
            log.warning(f" - Skipping activity detail {activity_detail['id']}.")
            ret['skipped_rows'] += 1
            continue

        if valid_activities_ids and new_activity_detail['activity_id'] not in valid_activities_ids:
            ret['skipped_rows'] += 1
            continue

        fields = new_activity_detail.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the activity detail ID exists
        sql = 'SELECT * FROM "activity_detail" WHERE id = %s'
        new_db.cursor.execute(sql, (activity_detail["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Activity detail {activity_detail['id']} already exists, updating the record")
            sql = f'UPDATE "activity_detail" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_activity_detail[field] for field in fields) + (activity_detail["id"],))
        else:
            sql = f'INSERT INTO "activity_detail" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_activity_detail[field] for field in fields))
        log.info(f" - Activity detail {activity_detail['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_activity_detail(activity_detail):
    """ Get an old db object and return a dict for the new DB object
        Old activity details looks like:
          {
            "id":"activity-detail-id",
            "activity_id":"activity-id",
            "object_id":"object-id",
            "object_type":"package",
            "activity_type":"changed package",
            "data":"{\"package\": {...}}"
        },
    """
    new_activity_detail = {
        'id': activity_detail['id'],
        'activity_id': activity_detail['activity_id'],
        'object_id': activity_detail['object_id'],
        'object_type': activity_detail['object_type'],
        'activity_type': activity_detail['activity_type'],
        'data': activity_detail['data']
    }

    return new_activity_detail
