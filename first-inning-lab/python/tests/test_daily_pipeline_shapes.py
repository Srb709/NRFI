from pathlib import Path

from first_inning_lab.pipelines import build_today_board as pipeline
from first_inning_lab.storage.json_store import read_json


def test_pipeline_empty_schedule_fallback(monkeypatch):
    monkeypatch.setattr(pipeline, "get_schedule", lambda _date: [])
    pipeline.run("2026-04-29")
    live = Path(pipeline.__file__).resolve().parents[3] / "data/live"
    board = read_json(live / "today_board.json", {})
    assert board.get("source") == "free_local_pipeline_fallback"
    assert board.get("summary", {}).get("games") == 0
