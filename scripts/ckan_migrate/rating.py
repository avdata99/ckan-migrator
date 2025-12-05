import logging


log = logging.getLogger(__name__)


def import_ratings(old_ratings, new_db):
    """ Get all old ratings from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing ratings...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    for rating in old_ratings:
        ret['total_rows'] += 1
        log.info(f"Importing rating: {rating['id']} (package: {rating['package_id']})")
        new_rating = transform_rating(rating)
        if not new_rating:
            log.warning(f" - Skipping rating {rating['id']}.")
            ret['skipped_rows'] += 1
            continue

        fields = new_rating.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the rating ID exists
        sql = 'SELECT * FROM "rating" WHERE id = %s'
        new_db.cursor.execute(sql, (rating["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Rating {rating['id']} already exists, updating the record")
            sql = f'UPDATE "rating" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_rating[field] for field in fields) + (rating["id"],))
        else:
            sql = f'INSERT INTO "rating" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_rating[field] for field in fields))
        log.info(f" - Rating {rating['id']} imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_rating(rating):
    """ Get an old db object and return a dict for the new DB object
        Old ratings looks like:
          {
            "id":"rating-id",
            "user_id":"user-id",
            "user_ip_address":"192.168.1.1",
            "package_id":"package-id",
            "rating":4.5,
            "created":"2017-03-21 18:23:56.055936"
        },
    """
    new_rating = {
        'id': rating['id'],
        'user_id': rating['user_id'],
        'user_ip_address': rating['user_ip_address'],
        'package_id': rating['package_id'],
        'rating': rating['rating'],
        'created': rating['created']
    }

    return new_rating
