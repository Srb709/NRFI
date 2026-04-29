from first_inning_lab.features.offense_features import build_offense_features
from first_inning_lab.features.park_weather_features import build_park_weather_features
from first_inning_lab.features.pitcher_features import build_pitcher_features


def test_pitcher_missing_neutral_warning():
    out = build_pitcher_features(None, None, 2026, "2026-04-29")
    assert out["pitcher_safety_score"] == 0.5 and out["warnings"]


def test_offense_missing_neutral_warning():
    out = build_offense_features(None, "Team", None, None, 2026, "2026-04-29")
    assert out["offense_danger_score"] == 0.5 and out["warnings"]


def test_park_weather_missing_weather_unavailable_score():
    out = build_park_weather_features({"venue_id": None}, {}, {"source": "unavailable", "available": False})
    assert out["park_weather_score"] is None and out["park_factor_available"] is False
