from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langchain_community.vectorstores import Chroma

from utils.config import load_config
from utils.telemetry import get_logger
from utils.embeddings import build_embeddings
from utils.results import save_stage_result

from rag_pipeline import (
    stage_02_retrieve, 
    stage_03_translate, 
    stage_04_route, 
    stage_05_sqlgen, 
    stage_06_execute, 
    stage_07_postprocess
)


api = FastAPI(title="NL2SQL Local API")
cfg = load_config()
_vs = None
log = get_logger(cfg.app.log_dir, "server")


class AskRequest(BaseModel):
    question: str


@api.on_event("startup")
def _init():
    global _vs
    
    try:
        _vs = Chroma(
            persist_directory=cfg.app.chroma_dir,
            embedding_function=build_embeddings(cfg.models.embedding),
        )
        log.info(f"Chroma loaded from {cfg.app.chroma_dir}")
    except Exception as e:
        log.error(f"Failed to load Chroma: {e}")
        _vs = None


@api.get("/health")
def health():
    return {"status": "ok"}


@api.post("/ask")
def ask(req: AskRequest):
    if _vs is None:
        raise HTTPException(status_code=503, detail="Chroma not initialized. Run ingestion first.")
    
    try:
        schema_context, docs = stage_02_retrieve.run(_vs, req.question, cfg)
        
        # build table summaries from retrieved docs
        tbl_summaries = {d.metadata.get("table", f"t{i}"): d.page_content[:300] for i, d in enumerate(docs)}
        rewrite = stage_03_translate.run(req.question, schema_context, cfg)
        tables, join_hints = stage_04_route.run(rewrite["rewritten"], tbl_summaries, cfg)
        
        sql = stage_05_sqlgen.run(rewrite["rewritten"], schema_context, tables, join_hints, cfg)
        
        result = stage_06_execute.run(sql, cfg)
        final = stage_07_postprocess.run(result, cfg)
        
        response = {
            "sql": sql,
            "result": final,
            "rewrite": rewrite,
            "tables": tables,
            "join_hints": join_hints,
        }

        save_stage_result("api_ask", response, cfg)
        log.info(f"API /ask succeeded for question: {req.question}")
        return response
    except Exception as e:
        log.error(f"API /ask failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
