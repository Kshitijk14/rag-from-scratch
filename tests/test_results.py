import json

from pathlib import Path

from utils.config import load_config
from utils.results import save_stage_result


def test_save_stage_result(tmp_path):
    # normalize win paths
    art_dir = str(tmp_path).replace("\\", "/")
    chroma_dir = str(tmp_path / "chroma").replace("\\", "/")
    log_dir = str(tmp_path / "logs").replace("\\", "/")
    
    # Create fake config
    cfg_text = f"""
        app:
            artifacts_dir: "{art_dir}"
            chroma_dir: "{chroma_dir}"
            log_dir: "{log_dir}"
        models:
            llm: "phi3:mini"
            temp: 0
            embedding: "sentence-transformers/all-MiniLM-L6-v2"
            ollama_base_url: "http://localhost:11434"
        retrieval:
            chunk_size: 100
            chunk_overlap: 10
            k: 2
            score_threshold: 0.1
        sql:
            dialect: oracle
            enforce_readonly: true
            row_limit: 10
        oracle:
            host: dummy
            port: 1521
            service_name: testdb
            user_env_key: USER
            pass_env_key: PASS
    """
    cfg_path = tmp_path / "params.yaml"
    cfg_path.write_text(cfg_text, encoding="utf-8")

    cfg = load_config(str(cfg_path))

    # Run and verify
    result_path = save_stage_result("stage_99_test", {"sample": 123}, cfg)
    file = Path(result_path)
    assert file.exists(), "Result file should be created"
    
    data = json.loads(file.read_text())
    assert data["sample"] == 123
    assert "stage_99_test" in file.name
