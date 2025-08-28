from scripts.db import PSQL


def test_extract_all_generates_files(tmp_path, pg_old, monkeypatch):
    # pg_old viene como (container, dsn)
    pg, dsn = pg_old
    host_port = pg.get_exposed_port(5432)
    dbname = dsn.split("/")[-1]

    db = PSQL(host="localhost", port=int(host_port), dbname=dbname, user="test", password="test")
    assert db.connect()

    # redirigir salida a tmp
    monkeypatch.chdir(tmp_path)
    db.extract_all_data(save_data=True)

    assert (tmp_path / "database_report.md").exists()
    assert (tmp_path / "tables_info.json").exists()
