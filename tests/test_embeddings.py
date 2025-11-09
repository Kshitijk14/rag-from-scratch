from utils.embeddings import build_embeddings


def test_build_embeddings_cache():
    emb1 = build_embeddings("sentence-transformers/all-MiniLM-L6-v2")
    emb2 = build_embeddings("sentence-transformers/all-MiniLM-L6-v2")
    assert emb1 is emb2  # cached
    vec = emb1.embed_query("hello world")
    assert isinstance(vec, list)
    assert len(vec) > 100
