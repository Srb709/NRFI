from first_inning_lab.utils.collections import dedupe_preserve_order
from first_inning_lab.features.assemble_game_features import assemble_game_features


def test_warning_dedupe():
    assert dedupe_preserve_order(["a", "b", "a"]) == ["a", "b"]


def test_data_quality_reflects_availability(monkeypatch):
    monkeypatch.setattr('first_inning_lab.features.assemble_game_features.get_pitcher_stats', lambda *a, **k: {"available": False, "warnings": [], "features": {}})
    monkeypatch.setattr('first_inning_lab.features.assemble_game_features.get_team_offense_stats', lambda *a, **k: {"available": False, "warnings": [], "features": {}})
    monkeypatch.setattr('first_inning_lab.features.assemble_game_features.get_lineup_data', lambda *a, **k: {"lineups_confirmed": False, "warnings": []})
    monkeypatch.setattr('first_inning_lab.features.assemble_game_features.build_park_weather_features', lambda *a, **k: {"park_weather_score": None, "park_factor_available": False})
    out = assemble_game_features({"game_id": "1"}, 2026, {}, {"source": "neutral_fallback"})
    assert out["data_quality_score"] < 0.7
