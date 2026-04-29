from pathlib import Path

from first_inning_lab.pipelines import build_today_board as pipeline
from first_inning_lab.storage.json_store import read_json


def test_pipeline_empty_schedule_fallback(monkeypatch):
    monkeypatch.setattr(pipeline, 'get_schedule', lambda _date: [])
    pipeline.run('2026-04-29')
    live = Path(pipeline.__file__).resolve().parents[3] / 'data/live'
    board = read_json(live / 'today_board.json', {})
    for key in ['generated_at', 'date', 'source', 'board_status', 'games', 'predictions', 'warnings', 'summary']:
      assert key in board
