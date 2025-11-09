import re

from utils.telemetry import get_logger
from utils.llm import build_llm
from utils.prompts import SQL_PROMPT
from utils.results import save_stage_result


def run(rewritten: str, schema_context: str, tables: list, join_hints: list, cfg) -> str:
    """
    Generate an Oracle SQL query based on the rewritten question and schema context.
    Includes validation, logging, and guardrails for malformed outputs.
    """
    log = get_logger(cfg.app.log_dir, "stage_05")
    
    # 1. initialize local llm
    llm = build_llm(
        cfg.models.llm, 
        cfg.models.temp
    )
    
    # Construct input payload
    inputs = {
        "schema_context": schema_context,
        "rewritten": rewritten,
        "tables": ", ".join(tables),
        "join_hints": "; ".join(join_hints) if join_hints else "",
    }
    log.info(f"SQLGen invoked for tables={tables} | joins={join_hints}")
    
    
    try:
        # Run prompt chain
        out = (SQL_PROMPT | llm).invoke(inputs)
        sql_text = getattr(out, "content", str(out)).strip()

        # Guard 1 — check empty / non-SQL responses
        if not sql_text or not sql_text.lower().startswith("select"):
            log.warning("LLM returned malformed SQL, attempting recovery.")
            
            # Try to extract SELECT statement via regex
            m = re.search(r"(?i)(select[\\s\\S]+?)(?:;|$)", sql_text)
            if m:
                sql_text = m.group(1).strip()
            else:
                raise ValueError("Model did not return valid SQL syntax.")
    except Exception as e:
        log.error(f"SQL generation failed: {e}")
        raise RuntimeError(f"SQL generation failed: {e}")

    log.info(f"Final SQL:\n{sql_text}")
    
    save_stage_result("stage_05_sqlgen", {"sql": sql_text}, cfg)
    return sql_text