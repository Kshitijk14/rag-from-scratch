import re
import json

from utils.telemetry import get_logger
from utils.llm import build_llm
from utils.prompts import REWRITE_PROMPT
from utils.results import save_stage_result


def run(question: str, schema_context: str, cfg):
    log = get_logger(cfg.app.log_dir, "stage_03")
    
    llm = build_llm(
        cfg.models.llm, 
        cfg.models.temp
    )
    
    chain = REWRITE_PROMPT | llm
    out = chain.invoke({"schema_context": schema_context, "question": question})
    
    try:
        data = json.loads(out.content if hasattr(out, "content") else str(out))
    except Exception:
        # fallback: try to extract JSON
        try:
            m = re.search(r"\{(?:[^{}]|(?R))*\}", str(out))
        except Exception:
            m = re.search(r"\{.*\}", str(out), re.DOTALL)
        
        data = json.loads(m.group(0)) if m else {"intent": "", "sub_questions": [], "rewritten": question}
        log.info(f"Intent={data.get('intent')} | SubQ={len(data.get('sub_questions', []))}")
        
        save_stage_result("stage_03_translate", data, cfg)
    return data
