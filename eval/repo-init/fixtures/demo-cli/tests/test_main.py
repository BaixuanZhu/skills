"""demo_cli 主入口测试。"""

from demo_cli.main import summarize


def test_summarize_empty():
    assert summarize([]) == {"count": 0, "total": 0}


def test_summarize_basic():
    rows = [{"amount": "10"}, {"amount": "20.5"}]
    assert summarize(rows) == {"count": 2, "total": 30.5}
