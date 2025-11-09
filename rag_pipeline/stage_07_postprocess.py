from typing import Dict, Any

from utils.results import save_stage_result


def run(result: Dict[str, Any], cfg):
    # pretty-print style; transform to dict list if needed
    rows = [dict(zip(result["columns"], r)) for r in result["rows"]]
    if not result.get("rows"):
        return {"columns": result.get("columns", []), "rows": []}

    save_stage_result("stage_07_postprocess", {"rows": len(rows)}, cfg)
    return {"columns": result["columns"], "rows": rows}