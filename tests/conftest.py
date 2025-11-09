import os
import tempfile
import shutil
import yaml
import pytest

from pathlib import Path


@pytest.fixture(scope="session")
def tmp_artifacts(tmp_path_factory):
    root = tmp_path_factory.mktemp("artifacts")
    for sub in ["logs", "chroma"]:
        (root / sub).mkdir(exist_ok=True)
    yield root
    shutil.rmtree(root, ignore_errors=True)

@pytest.fixture(scope="session")
def sample_config(tmp_artifacts):
    cfg = {
        "app": {
            "artifacts_dir": str(tmp_artifacts),
            "chroma_dir": str(tmp_artifacts / "chroma"),
            "log_dir": str(tmp_artifacts / "logs"),
        },
        "models": {
            "llm": "phi3:mini",
            "embedding": "sentence-transformers/all-MiniLM-L6-v2",
            "ollama_base_url": "http://localhost:11434",
        },
        "retrieval": {"chunk_size": 100, "chunk_overlap": 10, "k": 2, "score_threshold": 0.15},
        "sql": {"dialect": "oracle", "enforce_readonly": True, "row_limit": 10},
        "oracle": {
            "host": "mockhost",
            "port": 1521,
            "service_name": "orcl",
            "user_env_key": "DB_USER",
            "pass_env_key": "DB_PASS",
        },
    }
    file = tmp_artifacts / "params.yaml"
    yaml.safe_dump(cfg, open(file, "w"))
    os.environ.update({"DB_USER": "x", "DB_PASS": "y"})
    return file
