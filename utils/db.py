import re
import oracledb

from contextlib import contextmanager

from .config import load_config

cfg = load_config()


READONLY_PATTERN = re.compile(
    r"^\s*select\b", 
    re.IGNORECASE
)
FORBIDDEN = re.compile(
    r"(?i)\b(insert|update|delete|merge|alter|drop|truncate|create|grant|revoke)\b"
)


def make_dsn(host: str, port: int, service_name: str) -> str:
    return oracledb.makedsn(host=host, port=port, service_name=service_name)


@contextmanager
def oracle_conn(user: str, password: str, dsn: str):
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    
    try:
        yield conn
    finally:
        conn.close()


def safe_execute_sql(conn, sql: str, row_limit: int = cfg.sql.row_limit):
    """Safely execute a read-only Oracle SQL query."""
    if FORBIDDEN.search(sql) or not READONLY_PATTERN.search(sql):
        raise ValueError("Only read-only SELECT queries are allowed.")
    
    # apply row limit if not present
    if 'rownum' not in sql.lower():
        sql = f"SELECT * FROM ({sql}) WHERE ROWNUM <= {row_limit}"
    
    try:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return {"columns": cols, "rows": rows}
    except Exception as e:
        raise RuntimeError(f"SQL execution failed: {e}")