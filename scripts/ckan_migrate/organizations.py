import logging
from .helpers import ensure_unique_name

log = logging.getLogger(__name__)

FIELDS = [
    'id', 'name', 'title', 'description', 'created', 'state', 'type',
    'approval_status', 'image_url', 'is_organization'
]

def _transform(row):
    return {
        'id': row['id'],
        'name': row['name'],
        'title': row.get('title'),
        'description': row.get('description'),
        'created': row.get('created'),
        'state': (row.get('state') or 'active'),
        'type': (row.get('type') or 'organization'),
        'approval_status': row.get('approval_status'),
        'image_url': row.get('image_url'),
        'is_organization': True,
    }

def _upsert(new_db, gdict):
    placeholders = ', '.join(['%s'] * len(FIELDS))
    set_cols = ', '.join(FIELDS)

    new_db.cursor.execute('SELECT 1 FROM public."group" WHERE id = %s', (gdict['id'],))
    if new_db.cursor.fetchone():
        sql = f'UPDATE public."group" SET ({set_cols}) = ({placeholders}) WHERE id = %s'
        new_db.cursor.execute(sql, tuple(gdict[f] for f in FIELDS) + (gdict['id'],))
    else:
        sql = f'INSERT INTO public."group" ({set_cols}) VALUES ({placeholders})'
        new_db.cursor.execute(sql, tuple(gdict[f] for f in FIELDS))

def import_organizations(old_db, new_db):
    """
    Importa SOLO organizaciones (is_organization = true).
    """
    ret = {
        'total_rows': 0, 'migrated_rows': 0, 'skipped_rows': 0,
        'warnings': [], 'errors': [], 'ids': set()
    }

    log.info("Fetching organizations from old database...")
    old_db.cursor.execute('SET search_path TO public')
    new_db.cursor.execute('SET search_path TO public')

    old_db.cursor.execute('SELECT * FROM public."group" WHERE is_organization = TRUE')
    rows = old_db.cursor.fetchall()

    new_db.cursor.execute('SELECT name FROM public."group"')
    names_in_use = {r['name'] for r in new_db.cursor.fetchall()}
    def _taken(n): return n in names_in_use

    log.info(f" - Importing Organizations... ({len(rows)} registros)")
    for r in rows:
        ret['total_rows'] += 1
        g = _transform(r)

        # nombre único
        adjusted = ensure_unique_name(g['name'], _taken, suffix_seed=g['id'])
        if adjusted != g['name']:
            ret['warnings'].append(f"Organization '{g['name']}' renamed to '{adjusted}'")
            g['name'] = adjusted

        try:
            _upsert(new_db, g)
            names_in_use.add(g['name'])
            ret['migrated_rows'] += 1
            ret['ids'].add(g['id'])
        except Exception as e:
            ret['errors'].append(f"Organization id={g['id']} name={g['name']}: {e}")
            ret['skipped_rows'] += 1

    new_db.conn.commit()
    return ret
