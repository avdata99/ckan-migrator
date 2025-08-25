import types
from scripts.ckan_migrate.user import import_users


class FakeCursor:

    def __init__(self):
        self.queries = []
        self.data = [{"id":"1","name":"n1","fullname":"f1","email":"e1","created":None,"state":"active"}]

    def execute(self, q, params=None):
        self.queries.append((q, params))

    def fetchall(self):
        # simulate SELECT * from "user"
        return self.data


class FakeDB:
    def __init__(self):
        self.cursor = FakeCursor()
        self.conn = types.SimpleNamespace(commit=lambda: None)


def test_import_users_runs_inserts():
    old_db, new_db = FakeDB(), FakeDB()
    log = import_users(old_db, new_db)
    assert log["migrated_rows"] == 1
    # verificá que intentó upsert (insert/update) en new_db
    assert any('INSERT INTO "user"' in q for (q, _) in new_db.cursor.queries)
