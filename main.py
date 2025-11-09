import os
import json
import typer
import glob

from langchain_community.vectorstores import Chroma

from utils.config import load_config
from utils.telemetry import get_logger
from utils.embeddings import build_embeddings
from utils.results import save_stage_result

from rag_pipeline import (
    stage_01_ingest, 
    stage_02_retrieve, 
    stage_03_translate, 
    stage_04_route, 
    stage_05_sqlgen, 
    stage_06_execute, 
    stage_07_postprocess
)


app = typer.Typer(add_completion=False)


@app.command()
def ingest(schema_dir: str = typer.Option("schemas", help="Folder with *.sql or *.txt DDLs")):
    cfg = load_config()
    log = get_logger(cfg.app.log_dir)
    
    # discover schema files
    files = glob.glob(f"{schema_dir}/*.sql") + glob.glob(f"{schema_dir}/*.txt")
    
    # optional summaries file
    summaries_path = f"{schema_dir}/summaries.json"
    summaries = json.load(open(summaries_path)) if os.path.exists(summaries_path := summaries_path) else {}
    
    stage_01_ingest.run(files, summaries, cfg)
    log.info("Ingestion complete.")


@app.command()
def ask(question: str):
    cfg = load_config()
    log = get_logger(cfg.app.log_dir)
    
    if not os.path.exists(cfg.app.chroma_dir):
        raise FileNotFoundError(f"Chroma index not found at {cfg.app.chroma_dir}. Run `python main.py ingest` first.")
    
    vs = Chroma(
        persist_directory=cfg.app.chroma_dir, 
        embedding_function=build_embeddings(cfg.models.embedding)
    )

    schema_context, docs = stage_02_retrieve.run(vs, question, cfg)
    rewrite = stage_03_translate.run(question, schema_context, cfg)
    
    tables, join_hints = stage_04_route.run(
        rewrite["rewritten"], 
        {d.metadata.get("table", f"t{i}"): d.page_content[:300] for i, d in enumerate(docs)}, 
        cfg
    )
    
    sql = stage_05_sqlgen.run(rewrite["rewritten"], schema_context, tables, join_hints, cfg)
    result = stage_06_execute.run(sql, cfg)
    final = stage_07_postprocess.run(result, cfg)

    out = {
        "question": question,
        "intent": rewrite.get("intent"),
        "sub_questions": rewrite.get("sub_questions"),
        "rewritten": rewrite.get("rewritten"),
        "tables": tables,
        "sql": sql,
        "result": final,
    }
    
    save_stage_result("cli_ask", out, cfg)
    print(json.dumps(out, indent=2))
    log.info("Query complete.")


if __name__ == "__main__":
    app()
