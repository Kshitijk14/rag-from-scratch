from utils.config import get_env
from utils.telemetry import get_logger
from utils.db import make_dsn, oracle_conn, safe_execute_sql
from utils.results import save_stage_result


def run(sql: str, cfg):
    log = get_logger(cfg.app.log_dir, "stage_06")
    
    dsn = make_dsn(cfg.oracle.host, cfg.oracle.port, cfg.oracle.service_name)
    if not all([cfg.oracle.host, cfg.oracle.port, cfg.oracle.service_name]):
        raise ValueError("Oracle connection config incomplete.")

    user = get_env(cfg.oracle.user_env_key)
    pwd = get_env(cfg.oracle.pass_env_key)
    
    if not user or not pwd:
        raise RuntimeError("DB credentials not found in environment.")
    
    log.info(f"Executing SQL on {cfg.oracle.service_name}")
    with oracle_conn(user, pwd, dsn) as conn:
        result = safe_execute_sql(conn, sql, row_limit=cfg.sql.row_limit)
    
    save_stage_result("stage_06_execute", result, cfg)
    return result