from pathlib import Path
from typing import List, Dict

from langchain_core.documents import Document

from utils.telemetry import get_logger
from utils.embeddings import build_embeddings
from utils.retriever import build_splitter, build_vectorstore
from utils.results import save_stage_result


def run(schema_files: List[str], summaries: Dict[str, str], cfg):
    """Load table DDLs/summaries into Chroma."""
    log = get_logger(cfg.app.log_dir, "stage_01")
    splitter = build_splitter(cfg.retrieval.chunk_size, cfg.retrieval.chunk_overlap)
    embs = build_embeddings(cfg.models.embedding)

    docs: List[Document] = []
    for path in schema_files:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
        
        if not txt.strip():
            log.warning(f"Empty schema file skipped: {path}")
            continue
        
        tbl = Path(path).stem.split(".")[0]
        meta = {"table": tbl, "kind": "ddl"}
        docs.append(Document(page_content=txt, metadata=meta))

    for table, summary in summaries.items():
        docs.append(Document(page_content=summary, metadata={"table": table, "kind": "summary"}))

    # chunk
    docs = splitter.split_documents(docs)
    vs = build_vectorstore(docs, embs, cfg.app.chroma_dir)
    
    log.info(f"Indexed {len(docs)} chunks into Chroma at {cfg.app.chroma_dir}")
    
    save_stage_result("stage_01_ingest", {"docs_indexed": len(docs)}, cfg)
    return vs
