import logging


log = logging.getLogger(__name__)


def import_term_translations(old_db, new_db):
    """ Get all old term translations from DB and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Getting term translations from old database...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': []
    }
    query = 'SELECT * from "term_translation" ORDER BY term, lang_code'
    old_db.cursor.execute(query)
    term_translations = old_db.cursor.fetchall()

    for term_translation in term_translations:
        ret['total_rows'] += 1
        log.info(f"Importing term translation: {term_translation['term']} ({term_translation['lang_code']})")
        new_term_translation = transform_term_translation(term_translation)
        if not new_term_translation:
            log.warning(f" - Skipping term translation {term_translation['term']} ({term_translation['lang_code']}).")
            ret['skipped_rows'] += 1
            continue

        fields = new_term_translation.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the term translation exists (composite primary key)
        sql = 'SELECT * FROM "term_translation" WHERE term = %s AND lang_code = %s'
        new_db.cursor.execute(sql, (term_translation["term"], term_translation["lang_code"]))
        if new_db.cursor.fetchone():
            log.warning(
                (
                    f" - Term translation {term_translation['term']} "
                    f"({term_translation['lang_code']}) already exists, updating the record"
                )
            )
            sql = f'UPDATE "term_translation" SET ({", ".join(fields)}) = ({placeholders}) WHERE term= %s AND lang_code= %s'
            new_db.cursor.execute(
                sql,
                tuple(
                    new_term_translation[field] for field in fields
                ) + (
                    term_translation["term"], term_translation["lang_code"]
                )
            )
        else:
            sql = f'INSERT INTO "term_translation" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_term_translation[field] for field in fields))
        log.info(f" - Term translation {term_translation['term']} ({term_translation['lang_code']}) imported successfully.")
        ret['migrated_rows'] += 1

    new_db.conn.commit()
    return ret


def transform_term_translation(term_translation):
    """ Get an old db object and return a dict for the new DB object
        Old term translations looks like:
          {
            "term":"dataset",
            "term_translation":"conjunto de datos",
            "lang_code":"es"
        },
    """
    new_term_translation = {
        'term': term_translation['term'],
        'term_translation': term_translation['term_translation'],
        'lang_code': term_translation['lang_code']
    }

    return new_term_translation
