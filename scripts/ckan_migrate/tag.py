import logging


log = logging.getLogger(__name__)


def import_tags(old_tags, new_db):
    """ Get all old tags from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing tags...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    # Handle potential duplicate names
    names_in_use = []
    for tag in old_tags:
        ret['total_rows'] += 1
        log.info(f"Importing tag: {tag['name']}")
        new_tag = transform_tag(tag)
        if not new_tag:
            log.warning(f" - Skipping tag {tag['name']}.")
            ret['skipped_rows'] += 1
            continue

        # Check for duplicate names within the same vocabulary
        unique_key = f"{new_tag['name']}_{new_tag.get('vocabulary_id', 'no_vocab')}"
        if unique_key in names_in_use:
            # Add a suffix to the name
            original_name = new_tag['name']
            new_tag['name'] = f"{original_name}_{hash(tag['id'])}"
            ret['errors'].append(
                f" - Tag '{original_name}' has a duplicate name in the same vocabulary."
                f" New name: {new_tag['name']} (old: {original_name})"
            )

        fields = new_tag.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the tag ID exists
        sql = 'SELECT * FROM "tag" WHERE id = %s'
        new_db.cursor.execute(sql, (tag["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Tag {tag['name']} already exists, updating the record")
            sql = f'UPDATE "tag" SET ({', '.join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_tag[field] for field in fields) + (tag["id"],))
        else:
            sql = f'INSERT INTO "tag" ({', '.join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_tag[field] for field in fields))
        log.info(f" - Tag {tag['name']} imported successfully.")
        names_in_use.append(unique_key)
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_tag(tag):
    """ Get an old db object and return a dict for the new DB object
        Old tags looks like:
          {
            "id":"tag-id",
            "name":"tag-name",
            "vocabulary_id":"vocabulary-id"
        },
    """
    new_tag = {
        'id': tag['id'],
        'name': tag['name'],
        'vocabulary_id': tag['vocabulary_id']
    }

    return new_tag
