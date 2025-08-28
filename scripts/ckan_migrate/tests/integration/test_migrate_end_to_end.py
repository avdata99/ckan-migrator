from scripts.db import PSQL
from scripts.ckan_migrate.user import import_users
from scripts.ckan_migrate.groups import import_groups
from scripts.ckan_migrate.organizations import import_organizations
import psycopg2.extras


def _psql(pg, dbname=None, user="test", password="test"):
    host = "localhost"
    port = int(pg.get_exposed_port(5432))
    return PSQL(host=host, port=port, dbname=dbname, user=user, password=password)


def test_full_migrate_users_groups_orgs(pg_old, pg_new):
    # fixtures vienen como (container, dsn)
    old_pg, old_dsn = pg_old
    new_pg, new_dsn = pg_new

    old_dbname = old_dsn.split("/")[-1]
    new_dbname = new_dsn.split("/")[-1]

    old_db = _psql(old_pg, dbname=old_dbname)
    new_db = _psql(new_pg, dbname=new_dbname)
    assert old_db.connect() and new_db.connect()

    old_db.cursor = old_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    new_db.cursor = new_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    import_users(old_db, new_db)
    import_groups(old_db, new_db)
    import_organizations(old_db, new_db)

    new_db.conn.commit()
    new_db.cursor.execute('SELECT count(*) FROM "user"')
    assert new_db.cursor.fetchone()["count"] >= 2
    new_db.cursor.execute('SELECT count(*) FROM "group" WHERE is_organization=true')
    assert new_db.cursor.fetchone()["count"] >= 1
