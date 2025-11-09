import json

from utils.telemetry import get_logger
from utils.llm import build_llm
from utils.prompts import ROUTER_PROMPT
from utils.router import rule_based_route
from utils.results import save_stage_result


def run(rewritten: str, table_summaries: dict, cfg):
    """Decide which tables are relevant to a rewritten question (rule-based + LLM-assisted)."""
    log = get_logger(cfg.app.log_dir, "stage_04")
    
    # 1. rule-based routing
    rb = rule_based_route(rewritten, table_summaries)
    log.info(f"Rule-based route → {rb or 'none'}")

    llm_tables, join_hints = [], []
    
    # 2. LLM assist (only if rule-based fails or low confidence)
    if True:
        table_list = "\n".join(f"- {k}: {v[:180]}" for k, v in table_summaries.items())
        llm = build_llm(
            cfg.models.llm, 
            cfg.models.temp
        )

        out = (ROUTER_PROMPT | llm).invoke({
            "table_list": table_list,
            "rewritten": rewritten
        })

    # 3. parse LLM output (may be a string, dict, or object)
    text_out = getattr(out, "content", str(out))
    
    try:
        data = json.loads(text_out)
        llm_tables = data.get("tables", [])
        join_hints = data.get("join_hints", [])
        log.info(f"LLM route → tables={llm_tables}, joins={join_hints}")
    except Exception as e:
        log.warning(f"LLM router failed to parse JSON: {e}")
        llm_tables, join_hints = [], []

    # 4. union + dedupe (cap at 4)
    tables = list(dict.fromkeys([*rb, *llm_tables]))[:4]
    
    log.info(f"Final route → Tables={tables}, Joins={join_hints}")
    
    save_stage_result("stage_04_route", {"tables": tables, "join_hints": join_hints}, cfg)
    return tables, join_hints
