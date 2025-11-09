from typing import List

from utils.results import save_stage_result


def run(vs, question: str, cfg):
    retriever = vs.as_retriever(search_kwargs={"k": cfg.retrieval.k})
    
    docs: List = retriever.invoke(question)
    if not docs:
        raise ValueError("No schema fragments retrieved for this query.")
    
    schema_context = "\n\n".join(d.page_content for d in docs)
    
    save_stage_result("stage_02_retrieve", {"docs": [d.page_content for d in docs]}, cfg)
    return schema_context, docs
