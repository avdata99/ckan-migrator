import types
from scripts.ckan_migrate.user import import_users


class OldCursor:
    """Simula el cursor del OLD DB: devuelve una fila completa de user"""
    def __init__(self):
        self.queries = []
        # incluir TODOS los campos que usa transform_user
        self.data = [{
            "id": "1",
            "name": "n1",
            "fullname": "f1",
            "email": "e1",
            "about": "",
            "created": None,
            "sysadmin": False,
            "state": "active",
        }]

    def execute(self, q, params=None):
        self.queries.append((q, params))

    def fetchall(self):
        # simula: SELECT * from "user"
        return self.data


class NewCursor:
    """Simula el cursor del NEW DB: no existe el user todavía."""
    def __init__(self):
        self.queries = []
        self._last_select_exists = False

    def execute(self, q, params=None):
        self.queries.append((q, params))
        # heurística mínima para detectar el 'SELECT 1 FROM "user" WHERE id=%s'
        if 'FROM "user"' in q and 'WHERE id=' in q:
            self._last_select_exists = True
        else:
            self._last_select_exists = False

    def fetchone(self):
        # si se consultó por existencia, devolvemos None => no existe
        if self._last_select_exists:
            return None
        return None  # default

    def fetchall(self):
        return []


class FakeDB:
    def __init__(self, cursor):
        self.cursor = cursor
        self.conn = types.SimpleNamespace(commit=lambda: None)


def test_import_users_runs_inserts():
    old_db = FakeDB(OldCursor())
    new_db = FakeDB(NewCursor())

    log = import_users(old_db, new_db)

    assert log["migrated_rows"] == 1
    # verificá que intentó upsert (insert/update) en new_db
    assert any('INSERT INTO "user"' in q for (q, _) in new_db.cursor.queries) or \
           any('UPDATE "user"' in q for (q, _) in new_db.cursor.queries)
