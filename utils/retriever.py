from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .telemetry import get_logger


def build_vectorstore(docs, embeddings, persist_dir: str):
    if not docs:
        raise ValueError("No documents provided for vectorstore building.")
    
    log = get_logger(persist_dir, "retriever")
    vs = Chroma.from_documents(
        documents=docs, 
        embedding=embeddings, 
        persist_directory=persist_dir
    )
    
    # vs.persist() # auto-persist
    log.info(f"Successfully Indexed {len(docs)} chunks to {persist_dir}")
    return vs


def load_vectorstore(embeddings, persist_dir: str):
    """Open an existing Chroma collection on disk."""
    return Chroma(persist_directory=persist_dir, embedding_function=embeddings)

def add_to_vectorstore(vs: Chroma, docs):
    """Append more docs to an existing collection (auto-persist)."""
    if not docs:
        return 0
    vs.add_documents(docs)
    return len(docs)


def build_splitter(chunk_size: int, chunk_overlap: int):
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
