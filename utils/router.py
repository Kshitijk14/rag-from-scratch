import numpy as np
from typing import List, Dict

from .config import load_config
from .embeddings import build_embeddings

cfg = load_config()


def rule_based_route(rewritten: str, table_summaries: Dict[str, str]) -> List[str]:
    """Lightweight semantic routing using embedding similarity."""
    rewritten_emb = build_embeddings(cfg.models.embedding).embed_query(rewritten)
    table_embs = {
        t: build_embeddings(cfg.models.embedding).embed_query(s)
        for t, s in table_summaries.items()
    }
    sims = {
        t: float(np.dot(rewritten_emb, e) / (np.linalg.norm(rewritten_emb) * np.linalg.norm(e)))
        for t, e in table_embs.items()
    }
    top_tables = sorted(sims.items(), key=lambda x: x[1], reverse=True)[:4]
    return [t for t, _ in top_tables]