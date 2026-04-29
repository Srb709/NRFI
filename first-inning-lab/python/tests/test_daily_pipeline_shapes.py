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


def test_pipeline_uses_park_coordinates_for_weather(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.setattr(pipeline, 'get_schedule', lambda _date: [{
        'game_id': '1',
        'start_time': '2026-04-29T23:05:00Z',
        'venue_id': 10,
        'away_team_id': 1,
        'away_team': 'PHI',
        'home_team_id': 2,
        'home_team': 'NYM',
    }])
    monkeypatch.setattr(pipeline, 'read_json', lambda *_args, **_kwargs: [{'venue_id': 10, 'latitude': 40.75, 'longitude': -73.85}])

    def fake_weather(lat, lon, _start_time):
        captured['lat'] = lat
        captured['lon'] = lon
        return {'temperature_f': 70}

    monkeypatch.setattr(pipeline, 'get_game_weather', fake_weather)
    monkeypatch.setattr(pipeline, 'build_pitcher_features', lambda *_a, **_k: {})
    monkeypatch.setattr(pipeline, 'build_offense_features', lambda *_a, **_k: {})
    monkeypatch.setattr(pipeline, 'build_park_weather_features', lambda *_a, **_k: {})
    monkeypatch.setattr(pipeline, 'build_certainty_features', lambda *_a, **_k: {'board_status': 'EARLY'})
    monkeypatch.setattr(pipeline, 'combine_game_features', lambda *_a, **_k: {})
    monkeypatch.setattr(pipeline, 'predict_baseline', lambda *_a, **_k: {'lean': 'PASS', 'data_quality_score': 0.5})

    pipeline.run('2026-04-29')

    assert captured['lat'] == 40.75
    assert captured['lon'] == -73.85
