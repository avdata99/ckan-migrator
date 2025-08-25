from scripts.db import PSQL
from scripts.ckan_migrate.user import import_users
from scripts.ckan_migrate.groups import import_groups
from scripts.ckan_migrate.organizations import import_organizations
import psycopg2.extras


def _psql(pg, dbname=None, user="test", password="test"):
    host = "localhost"
    port = int(pg.get_exposed_port(5432))
    if not dbname:
        dbname = pg.get_connection_url().split("/")[-1]
    return PSQL(host=host, port=port, dbname=dbname, user=user, password=password)

def test_full_migrate_users_groups_orgs(pg_old, pg_new):
    old_db = _psql(pg_old)
    new_db = _psql(pg_new)
    assert old_db.connect() and new_db.connect()

    old_db.cursor = old_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    new_db.cursor = new_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    ulog = import_users(old_db, new_db)
    glog = import_groups(old_db, new_db)
    olog = import_organizations(old_db, new_db)

    # commit y verificaciones
    new_db.conn.commit()
    new_db.cursor.execute('SELECT count(*) FROM "user"')
    assert new_db.cursor.fetchone()["count"] >= 2
    new_db.cursor.execute('SELECT count(*) FROM "group" WHERE is_organization=true')
    assert new_db.cursor.fetchone()["count"] >= 1
