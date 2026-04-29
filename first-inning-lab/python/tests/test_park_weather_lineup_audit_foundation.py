import json
from pathlib import Path

from first_inning_lab.data_sources.lineup_provider import get_lineup_data
from first_inning_lab.data_sources.weather_client import get_game_weather
from first_inning_lab.features.park_weather_features import build_park_weather_features
from first_inning_lab.pipelines import audit_today_data


def test_park_factors_reference_shape():
    park_path = Path(__file__).resolve().parents[2] / "data/reference/park_factors.json"
    parks = json.loads(park_path.read_text(encoding="utf-8"))
    assert len(parks) == 30
    venue_ids = [p["venue_id"] for p in parks]
    team_ids = [p["team_id"] for p in parks]
    assert all(v is not None for v in venue_ids)
    assert len(set(venue_ids)) == len(venue_ids)
    assert len(set(team_ids)) == len(team_ids)
    assert all(p.get("roof_type") in {"open", "retractable", "dome", "unknown"} for p in parks)
    assert all((p.get("latitude") is not None and p.get("longitude") is not None) or p.get("notes") for p in parks)


def test_missing_park_entry_unavailable():
    out = build_park_weather_features({"venue_id": 9999}, {}, {"available": False, "source": "unavailable", "warnings": ["x"]})
    assert out["park_factor_available"] is False
    assert out["park_weather_score"] is None


def test_null_park_factors_unavailable():
    parks = {"1": {"run_factor": None, "hr_factor": None, "latitude": 1.0, "longitude": 2.0}}
    out = build_park_weather_features({"venue_id": 1}, parks, {"available": False, "source": "unavailable", "warnings": ["x"]})
    assert out["park_factor_available"] is False
    assert out["park_weather_score"] is None


def test_valid_park_factors_available():
    parks = {"1": {"run_factor": 1.05, "hr_factor": 1.02, "latitude": 1.0, "longitude": 2.0}}
    out = build_park_weather_features({"venue_id": 1}, parks, {"available": False, "source": "unavailable", "warnings": ["x"]})
    assert out["park_factor_available"] is True
    assert out["park_weather_score"] is not None


def test_weather_missing_coordinates_unavailable():
    out = get_game_weather(None, None, "2026-04-29T20:00:00Z")
    assert out["available"] is False
    assert out["source"] == "unavailable"
    assert out["weather_run_factor"] is None


def test_weather_nearest_hour_selection(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({
                "hourly": {
                    "time": ["2026-04-29T19:00", "2026-04-29T20:00", "2026-04-29T21:00"],
                    "temperature_2m": [10, 20, 30],
                    "precipitation_probability": [0, 10, 20],
                    "wind_speed_10m": [3, 4, 5],
                    "wind_direction_10m": [100, 110, 120],
                }
            }).encode("utf-8")

    monkeypatch.setattr("first_inning_lab.data_sources.weather_client.urlopen", lambda *_a, **_k: _Resp())
    out = get_game_weather(10.0, 10.0, "2026-04-29T20:20:00Z")
    assert out["available"] is True
    assert "20:00" in out["weather_summary"]


def test_lineup_fallback_to_boxscore(monkeypatch):
    monkeypatch.setattr("first_inning_lab.data_sources.lineup_provider.get_game_feed", lambda _g: {})
    monkeypatch.setattr(
        "first_inning_lab.data_sources.lineup_provider.get_boxscore",
        lambda _g: {
            "teams": {
                "away": {"players": {"ID1": {"battingOrder": "001", "person": {"id": 1, "fullName": "A1"}, "batSide": {"code": "R"}}, "ID2": {"battingOrder": "002", "person": {"id": 2, "fullName": "A2"}, "batSide": {"code": "L"}}, "ID3": {"battingOrder": "003", "person": {"id": 3, "fullName": "A3"}, "batSide": {"code": "R"}}}},
                "home": {"players": {"ID4": {"battingOrder": "001", "person": {"id": 4, "fullName": "H1"}, "batSide": {"code": "R"}}, "ID5": {"battingOrder": "002", "person": {"id": 5, "fullName": "H2"}, "batSide": {"code": "L"}}, "ID6": {"battingOrder": "003", "person": {"id": 6, "fullName": "H3"}, "batSide": {"code": "R"}}}},
            }
        },
    )
    out = get_lineup_data(1)
    assert out["lineups_confirmed"] is True
    assert out["source"] == "boxscore"
    assert out["diagnostics"]["away_batting_order_count"] >= 3


def test_audit_writes_file_and_counts(monkeypatch, tmp_path):
    monkeypatch.setattr(audit_today_data, "_root", lambda: tmp_path)
    (tmp_path / "data/reference").mkdir(parents=True)
    (tmp_path / "data/live").mkdir(parents=True)
    (tmp_path / "data/reference/park_factors.json").write_text(json.dumps([{"venue_id": 1, "run_factor": None, "hr_factor": None, "latitude": None, "longitude": None}]), encoding="utf-8")
    monkeypatch.setattr(audit_today_data, "get_schedule", lambda _d: [{"game": "A @ B", "game_id": "1", "game_pk": 1, "venue_id": 1, "venue": "V", "start_time": "2026-04-29T20:00:00Z"}])
    monkeypatch.setattr(audit_today_data, "get_game_weather", lambda *_a, **_k: {"available": False, "source": "unavailable", "warnings": ["w"]})
    monkeypatch.setattr(
        audit_today_data,
        "assemble_game_features",
        lambda *_a, **_k: {
            "feature_status": {
                "probable_pitchers_available": False,
                "pitcher_stats_available": False,
                "team_offense_stats_available": False,
                "park_factor_available": False,
                "weather_available": False,
                "lineups_confirmed": False,
            },
            "raw_features": {"park": {"stadium_coordinates_available": False}},
        },
    )
    audit_today_data.run("2026-04-29")
    out_path = tmp_path / "data/live/today_data_audit.json"
    assert out_path.exists()
    out = json.loads(out_path.read_text(encoding="utf-8"))
    assert out["counts"]["park_factor_missing"] == 1
    assert out["counts"]["weather_missing"] == 1
