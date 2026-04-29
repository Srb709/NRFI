from __future__ import annotations


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def combine_game_features(game, away_pitcher, home_pitcher, away_offense, home_offense, park_weather, certainty):
    warnings = []
    reasons = []
    for key in (away_pitcher, home_pitcher, away_offense, home_offense, park_weather, certainty):
        warnings.extend(key.get("warnings", []))
        reasons.extend(key.get("reasons", []))
    return {
        "game_id": game.get("game_id"),
        "pitcher_safety_score": _clamp((away_pitcher.get("pitcher_safety_score", 0.5) + home_pitcher.get("pitcher_safety_score", 0.5)) / 2),
        "offense_danger_score": _clamp((away_offense.get("offense_danger_score", 0.5) + home_offense.get("offense_danger_score", 0.5)) / 2),
        "park_weather_score": _clamp(park_weather.get("park_weather_score", 0.5)),
        "certainty_score": _clamp(certainty.get("data_quality_score", 0.5)),
        "data_quality_score": _clamp(certainty.get("data_quality_score", 0.5)),
        "recent_form_score": 0.5,
        "lineups_confirmed": certainty.get("lineups_confirmed", False),
        "starters_confirmed_or_probable": certainty.get("starters_confirmed_or_probable", False),
        "advanced_stats_available": away_pitcher.get("data_available", False) and home_pitcher.get("data_available", False),
        "bullpen_or_opener_risk": certainty.get("bullpen_or_opener_risk", True),
        "weather_flags": park_weather.get("flags", []),
        "warnings": warnings,
        "reasons": reasons,
    }
