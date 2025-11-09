from utils.telemetry import get_logger


def test_logger_creation(tmp_artifacts):
    logger = get_logger(tmp_artifacts / "logs", "test_logger")
    logger.info("hello world")
    assert logger.handlers
    assert any("FileHandler" in str(type(h)) for h in logger.handlers)
