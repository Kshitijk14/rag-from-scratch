from __future__ import annotations

import os 
import yaml

from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class AppConfig:
    artifacts_dir: str
    chroma_dir: str
    log_dir: str


@dataclass
class ModelConfig:
    llm: str
    embedding: str
    ollama_base_url: str
    temp: float = 0.0


@dataclass
class RetrievalConfig:
    chunk_size: int
    chunk_overlap: int
    k: int
    score_threshold: float


@dataclass
class SQLConfig:
    dialect: str
    enforce_readonly: bool
    row_limit: int


@dataclass
class OracleConfig:
    host: str
    port: int
    service_name: str
    user_env_key: str
    pass_env_key: str


@dataclass
class Config:
    app: AppConfig
    models: ModelConfig
    retrieval: RetrievalConfig
    sql: SQLConfig
    oracle: OracleConfig


def load_config(path: str = "params.yaml") -> Config:
    load_dotenv('.env.local')
    if not load_dotenv(".env.local"):
        load_dotenv(".env")
    
    if not Path(path).exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    
    for section in ["app", "models", "retrieval", "sql", "oracle"]:
        if section not in y:
            raise KeyError(f"Missing '{section}' section in {path}")
    
    app = AppConfig(**y["app"])
    models = ModelConfig(**y["models"])
    retrieval = RetrievalConfig(**y["retrieval"])
    sql = SQLConfig(**y["sql"])
    oracle = OracleConfig(**y["oracle"])
    
    # ensure dirs exist
    for p in [app.artifacts_dir, app.chroma_dir, app.log_dir]:
        Path(p).mkdir(parents=True, exist_ok=True)
    
    return Config(app, models, retrieval, sql, oracle)


# helpers
get_env = os.getenv