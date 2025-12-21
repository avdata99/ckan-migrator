import logging


log = logging.getLogger(__name__)


def import_vocabularies(old_vocabularies, new_db):
    """ Get all old vocabularies from CSV and import them """
    log.info("Importing vocabularies...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }

    # Handle potential duplicate names
    names_in_use = []
    for vocabulary in old_vocabularies:
        ret['total_rows'] += 1
        log.info(f"Importing vocabulary: {vocabulary['name']}")
        new_vocabulary = transform_vocabulary(vocabulary)
        if not new_vocabulary:
            log.warning(f" - Skipping vocabulary {vocabulary['name']}.")
            ret['skipped_rows'] += 1
            continue

        if new_vocabulary['name'] in names_in_use:
            # Add a suffix to the name
            original_name = new_vocabulary['name']
            new_vocabulary['name'] = f"{original_name}_{hash(vocabulary['id'])}"
            ret['errors'].append(
                f" - Vocabulary '{original_name}' has a duplicate name."
                f" New name: {new_vocabulary['name']} (old: {original_name})"
            )

        fields = new_vocabulary.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the vocabulary ID exists
        sql = 'SELECT * FROM "vocabulary" WHERE id = %s'
        new_db.cursor.execute(sql, (vocabulary["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Vocabulary {vocabulary['name']} already exists, updating the record")
            sql = f'UPDATE "vocabulary" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_vocabulary[field] for field in fields) + (vocabulary["id"],))
        else:
            sql = f'INSERT INTO "vocabulary" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_vocabulary[field] for field in fields))
        log.info(f" - Vocabulary {vocabulary['name']} imported successfully.")
        names_in_use.append(new_vocabulary['name'])
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_vocabulary(vocabulary):
    """ Get an old db object and return a dict for the new DB object
        Old vocabularies looks like:
          {
            "id":"vocabulary-id",
            "name":"vocabulary-name"
        },
    """
    new_vocabulary = {
        'id': vocabulary['id'],
        'name': vocabulary['name']
    }

    return new_vocabulary
