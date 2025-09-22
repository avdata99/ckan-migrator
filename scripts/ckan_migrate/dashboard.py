import logging


log = logging.getLogger(__name__)


def import_dashboards(old_db, new_db, valid_users_ids=None):
    """ Get all old dashboards from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting dashboards from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "dashboard"'
    old_db.cursor.execute(query)
    dashboards = old_db.cursor.fetchall()

    for dashboard in dashboards:
        ret['total_rows'] += 1
        log.info(f"Importing dashboard for user: {dashboard['user_id']}")
        new_dashboard = transform_dashboard(dashboard)
        if not new_dashboard:
            log.warning(f" - Skipping dashboard for user {dashboard['user_id']}.")
            ret['skipped_rows'] += 1
            continue

        if valid_users_ids and new_dashboard['user_id'] not in valid_users_ids:
            ret['skipped_rows'] += 1
            continue

        fields = new_dashboard.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the dashboard for this user exists
        sql = 'SELECT * FROM "dashboard" WHERE user_id = %s'
        new_db.cursor.execute(sql, (dashboard["user_id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Dashboard for user {dashboard['user_id']} already exists, updating the record")
            sql = f'UPDATE "dashboard" SET ({", ".join(fields)}) = ({placeholders}) WHERE user_id= %s'
            new_db.cursor.execute(sql, tuple(new_dashboard[field] for field in fields) + (dashboard["user_id"],))
        else:
            sql = f'INSERT INTO "dashboard" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_dashboard[field] for field in fields))
        log.info(f" - Dashboard for user {dashboard['user_id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_dashboard(dashboard):
    """ Get an old db object and return a dict for the new DB object
        Old dashboards looks like:
          {
            "user_id":"user-id",
            "activity_stream_last_viewed":"2017-03-21 18:23:56.055936",
            "email_last_sent":"2017-03-21 18:23:56.055936"
        },
    """
    new_dashboard = {
        'user_id': dashboard['user_id'],
        'activity_stream_last_viewed': dashboard['activity_stream_last_viewed'],
        'email_last_sent': dashboard['email_last_sent']
    }

    return new_dashboard
