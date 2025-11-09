from utils.llm import build_llm


def test_build_llm_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:1234")
    llm = build_llm("qwen3:0.6b", model_temp=0)
    assert hasattr(llm, "invoke")
    assert "qwen3" in llm.model
