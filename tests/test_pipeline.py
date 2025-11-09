import json
import pytest

from pathlib import Path

import rag_pipeline.stage_01_ingest as s1
import rag_pipeline.stage_02_retrieve as s2
import rag_pipeline.stage_03_translate as s3
import rag_pipeline.stage_04_route as s4
import rag_pipeline.stage_05_sqlgen as s5
import rag_pipeline.stage_06_execute as s6
import rag_pipeline.stage_07_postprocess as s7

from utils.config import load_config
from utils.results import save_stage_result


@pytest.fixture(scope="session")
def cfg(tmp_path_factory):
    """Create a mock config for the pipeline."""
    root = tmp_path_factory.mktemp("pipeline_artifacts")
    
    chroma = root / "chroma"
    logs = root / "logs"
    results = root / "results"
    for p in [chroma, logs, results]:
        p.mkdir(parents=True, exist_ok=True)

    cfg_path = root / "params.yaml"
    cfg_path.write_text(f"""
        app:
            artifacts_dir: "{root.as_posix()}"
            chroma_dir: "{chroma.as_posix()}"
            log_dir: "{logs.as_posix()}"
        models:
            llm: "mock-llm"
            temp: 0
            embedding: "sentence-transformers/all-MiniLM-L6-v2"
            ollama_base_url: "http://localhost:11434"
        retrieval:
            chunk_size: 100
            chunk_overlap: 10
            k: 1
            score_threshold: 0.1
        sql:
            dialect: oracle
            enforce_readonly: true
            row_limit: 10
        oracle:
            host: "dummyhost"
            port: 1521
            service_name: "testdb"
            user_env_key: "USER"
            pass_env_key: "PASS"
    """)
    return load_config(str(cfg_path))


@pytest.fixture
def mock_schema_files(tmp_path):
    ddl_path = tmp_path / "CUSTOMER.sql"
    ddl_path.write_text("CREATE TABLE CUSTOMER (ID INT, NAME VARCHAR(50));")
    return [str(ddl_path)]


@pytest.fixture
def mock_table_summaries():
    return {"CUSTOMER": "Customer master table with ID and NAME"}



# ------------------- MOCK HELPERS ------------------- #
@pytest.fixture(autouse=True)
def mock_db_env(monkeypatch):
    """Mock DB environment credentials so stage_06_execute passes."""
    monkeypatch.setenv("USER", "dummy_user")
    monkeypatch.setenv("PASS", "dummy_pass")
    yield


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """Mock ChatOllama across all stage modules to avoid real HTTP calls."""
    class MockLLM:
        def __init__(self, *args, **kwargs):
            pass
        
        # callable
        def __call__(self, inputs):
            # emulate the same behavior as invoke
            return self.invoke(inputs)
        
        def invoke(self, inputs, **kwargs):
            # handle all three prompt types
            if isinstance(inputs, dict) and "question" in inputs:
                return type("Obj", (), {
                    "content": '{"intent":"query","sub_questions":["A"],"rewritten":"show customers"}'
                })
            elif isinstance(inputs, dict) and "table_list" in inputs:
                return type("Obj", (), {
                    "content": '{"tables":["CUSTOMER"],"join_hints":[]}'
                })
            else:
                return type("Obj", (), {"content": "SELECT * FROM CUSTOMER"})

    # Patch build_llm globally
    def fake_build_llm(model_name, temp):
        return MockLLM()
    
    # Apply across all relevant namespaces
    monkeypatch.setattr("utils.llm.build_llm", fake_build_llm)
    monkeypatch.setattr("utils.llm.ChatOllama", MockLLM)
    monkeypatch.setattr("langchain_ollama.ChatOllama", MockLLM)
    
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:65501")

    yield


@pytest.fixture(autouse=True)
def mock_oracle(monkeypatch):
    """Mock the full Oracle connection layer so no real DB calls are made."""

    # Mock safe_execute_sql
    def fake_safe_execute_sql(conn, sql, row_limit):
        # sanity check
        assert sql.strip().lower().startswith("select"), (f"Non-SELECT query attempted: {sql}")
        return {"columns": ["ID", "NAME"], "rows": [(1, "Alice"), (2, "Bob")]}

    # Mock oracle_conn context manager
    class DummyCursor:
        def __init__(self):
            self.description = [("ID",), ("NAME",)]
        def execute(self, *a, **kw): return None
        def fetchall(self): return [(1, "Alice"), (2, "Bob")]
        def close(self): pass

    class DummyConn:
        def cursor(self): return DummyCursor()
        def close(self): pass

    from contextlib import contextmanager

    @contextmanager
    def fake_oracle_conn(user, pwd, dsn):
        yield DummyConn()
    
    def fake_make_dsn(host, port, service_name):
        return f"dsn://{host}:{port}/{service_name}"

    monkeypatch.setattr("utils.db.safe_execute_sql", fake_safe_execute_sql)
    monkeypatch.setattr("utils.db.oracle_conn", fake_oracle_conn)
    monkeypatch.setattr("utils.db.make_dsn", fake_make_dsn)
    monkeypatch.setattr(
        "utils.db.oracledb",
        type(
            "mock",
            (),
            {
                "makedsn": lambda **k: "dsn_string",
                "connect": lambda **k: DummyConn(),
            },
        ),
    )
    yield



# ------------------- TESTS ------------------- #
def test_full_pipeline(tmp_path, cfg, mock_schema_files, mock_table_summaries):
    # 1. Ingest
    vs = s1.run(mock_schema_files, mock_table_summaries, cfg)
    assert vs is not None

    # 2. Retrieve
    schema_context, docs = s2.run(vs, "Show customers", cfg)
    assert isinstance(schema_context, str)
    assert "customer" in schema_context.lower()
    assert isinstance(docs, list)
    assert len(docs) > 0

    # 3. Translate
    translate_data = s3.run("Show customers", schema_context, cfg)
    assert "rewritten" in translate_data

    # 4. Route
    tables, joins = s4.run(translate_data["rewritten"], mock_table_summaries, cfg)
    assert "CUSTOMER" in tables

    # 5. SQL Generation
    sql_text = s5.run(translate_data["rewritten"], schema_context, tables, joins, cfg)
    assert sql_text.lower().startswith("select")

    # 6. Execution
    result = s6.run(sql_text, cfg)
    assert "columns" in result and len(result["rows"]) == 2

    # 7. Postprocess
    post = s7.run(result, cfg)
    assert isinstance(post["rows"], list)
    assert post["rows"][0]["NAME"] == "Alice"

    # 8. Verify artifacts saved
    results_dir = Path(cfg.app.artifacts_dir) / "results"
    files = list(results_dir.glob("stage_*"))
    assert len(files) >= 7, f"Expected results for all stages, found {len(files)}"

    # Validate one JSON content
    sample_file = files[-1]
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, dict)
