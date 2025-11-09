from langchain_core.documents import Document

from utils.retriever import build_vectorstore, build_splitter
from utils.embeddings import build_embeddings


def test_build_splitter():
    splitter = build_splitter(100, 10)
    assert splitter is not None

def test_build_vectorstore(tmp_artifacts):
    docs = [Document(page_content="hello world", metadata={"t": "T1"})]
    emb = build_embeddings("sentence-transformers/all-MiniLM-L6-v2")
    vs = build_vectorstore(docs, emb, str(tmp_artifacts))
    assert hasattr(vs, "persist")
