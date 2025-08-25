from scripts.db import PSQL

def test_extract_all_generates_files(tmp_path, pg_old, monkeypatch):
    # conectar al PG old de testcontainers
    uri = pg_old.get_connection_url()
    parts = uri.split("/")
    dbname = parts[-1]
    host_port = pg_old.get_exposed_port(5432)
    db = PSQL(host="localhost", port=int(host_port), dbname=dbname, user="test", password="test")
    assert db.connect()
    # redirigir salida a tmp
    monkeypatch.chdir(tmp_path)
    db.extract_all_data(save_data=True)
    assert (tmp_path / "database_report.md").exists()
    assert (tmp_path / "tables_info.json").exists()
