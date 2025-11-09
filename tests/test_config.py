from utils.config import load_config


def test_load_config(tmp_artifacts, sample_config):
    cfg = load_config(str(sample_config))
    assert cfg.app.artifacts_dir
    assert cfg.models.llm.startswith("phi")
    assert cfg.sql.row_limit == 10
