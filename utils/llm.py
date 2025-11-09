from langchain_ollama import ChatOllama

from .config import load_config

cfg = load_config()


def build_llm(model_name: str, model_temp: float):
    
    llm = ChatOllama(
        base_url=cfg.models.ollama_base_url,
        model=model_name, 
        temperature=model_temp
    )
    
    return llm