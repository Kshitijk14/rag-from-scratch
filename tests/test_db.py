import pytest

from utils.db import READONLY_PATTERN, FORBIDDEN


def test_readonly_regex():
    assert READONLY_PATTERN.search("select * from dual")
    assert not READONLY_PATTERN.search("delete from dual")

def test_forbidden_regex_blocks():
    for kw in ["insert", "drop", "update"]:
        assert FORBIDDEN.search(f"{kw} something")

@pytest.mark.parametrize("sql,expected", [
    ("select * from dual", True),
    ("delete from dual", False)
])
def test_sql_pattern(sql, expected):
    assert bool(READONLY_PATTERN.search(sql)) == expected
