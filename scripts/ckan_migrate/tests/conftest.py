from urllib.parse import urlparse
import psycopg2
from testcontainers.postgres import PostgresContainer
from pathlib import Path
import pytest

SQL_DIR = Path(__file__).parent / "sql"

def _exec_sql(dsn, sql_path: Path):
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(sql_path.read_text())

def _sqlalchemy_url_to_psycopg2_dsn(url: str) -> str:
    """
    Convierte 'postgresql+psycopg2://user:pass@host:port/db' en
    'postgres://user:pass@host:port/db' para psycopg2.
    """
    # normalizamos: quitamos el '+psycopg2' y dejamos esquema 'postgres'
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(url)
    scheme = "postgres"  # psycopg2 acepta 'postgres://' o 'postgresql://'
    netloc = parsed.netloc  # user:pass@host:port
    path = parsed.path      # /dbname
    return f"{scheme}://{netloc}{path}"

@pytest.fixture(scope="session")
def pg_old():
    with PostgresContainer("postgres:9.6").with_env("POSTGRES_DB", "old_ckan_db") as pg:
        conn_url = pg.get_connection_url()  # p.ej. postgresql+psycopg2://test:test@localhost:32769/test
        dsn = _sqlalchemy_url_to_psycopg2_dsn(conn_url)
        _exec_sql(dsn, SQL_DIR / "old_minimal.sql")
        yield pg, dsn

@pytest.fixture(scope="session")
def pg_new():
    with PostgresContainer("postgres:15") as pg:
        conn_url = pg.get_connection_url()
        dsn = _sqlalchemy_url_to_psycopg2_dsn(conn_url)
        _exec_sql(dsn, SQL_DIR / "new_schema.sql")
        yield pg, dsn
