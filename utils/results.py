import json

from datetime import datetime
from pathlib import Path
from typing import Any, Union

from utils.telemetry import get_logger


def save_stage_result(stage_name: str, data: Union[dict, list, str, Any], cfg) -> str:
    """
    Save intermediate results from any pipeline stage to a JSON file under artifacts/results/.
    
    Args:
        stage_name (str): Name of the stage (e.g. "stage_03_translate").
        data (Any): Python object to serialize (dict, list, or string).
        cfg: Loaded global config (for artifacts dir path).

    Returns:
        str: Path to saved JSON file.
    """
    results_dir = Path(cfg.app.artifacts_dir) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize file name (stage only)
    safe_name = stage_name.replace("/", "_").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = results_dir / f"{safe_name}_{timestamp}.json"

    # Serialize safely
    try:
        if isinstance(data, (dict, list)):
            serialized = data
        elif isinstance(data, str):
            serialized = {"text": data}
        else:
            serialized = {"repr": repr(data)}

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)

        get_logger(cfg.app.log_dir, "results").info(f"Saved {stage_name} → {file_path}")
        return str(file_path)
    except Exception as e:
        get_logger(cfg.app.log_dir, "results").error(f"Failed to save result for {stage_name}: {e}")
        raise
