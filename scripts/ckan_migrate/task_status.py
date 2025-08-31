import logging


log = logging.getLogger(__name__)


def import_task_status(old_db, new_db):
    """ Get all old task status from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting task status from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "task_status" ORDER BY last_updated'
    old_db.cursor.execute(query)
    task_statuses = old_db.cursor.fetchall()

    for task_status in task_statuses:
        ret['total_rows'] += 1
        log.info(f"Importing task status: {task_status['id']} (type: {task_status['task_type']})")
        new_task_status = transform_task_status(task_status)
        if not new_task_status:
            log.warning(f" - Skipping task status {task_status['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_task_status.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the task status ID exists
        sql = 'SELECT * FROM "task_status" WHERE id = %s'
        new_db.cursor.execute(sql, (task_status["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Task status {task_status['id']} already exists, updating the record")
            sql = f'UPDATE "task_status" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_task_status[field] for field in fields) + (task_status["id"],))
        else:
            sql = f'INSERT INTO "task_status" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_task_status[field] for field in fields))
        log.info(f" - Task status {task_status['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_task_status(task_status):
    """ Get an old db object and return a dict for the new DB object
        Old task status looks like:
          {
            "id":"task-status-id",
            "entity_id":"entity-id",
            "entity_type":"package",
            "task_type":"archiver",
            "key":"status",
            "value":"success",
            "state":"active",
            "error":"error message",
            "last_updated":"2017-03-21 18:23:56.055936"
        },
    """
    new_task_status = {
        'id': task_status['id'],
        'entity_id': task_status['entity_id'],
        'entity_type': task_status['entity_type'],
        'task_type': task_status['task_type'],
        'key': task_status['key'],
        'value': task_status['value'],
        'state': task_status['state'],
        'error': task_status['error'],
        'last_updated': task_status['last_updated']
    }

    return new_task_status
