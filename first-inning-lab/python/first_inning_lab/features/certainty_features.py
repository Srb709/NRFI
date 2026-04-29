from __future__ import annotations


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def build_certainty_features(game, away_pitcher_features, home_pitcher_features, away_offense_features, home_offense_features, weather):
    warnings = []
    score = 1.0
    lineups_confirmed = bool(away_offense_features.get("lineup_confirmed")) and bool(home_offense_features.get("lineup_confirmed"))
    if not lineups_confirmed:
        score -= 0.20
        warnings.append("Lineups unconfirmed")
    starters_ok = bool(game.get("away_probable_pitcher_id")) and bool(game.get("home_probable_pitcher_id"))
    if not starters_ok:
        score -= 0.35
        warnings.append("Missing probable pitcher")
    weather_available = bool(weather) and weather.get("source") != "neutral_fallback"
    if not weather_available:
        score -= 0.10
        warnings.append("Weather fallback used")
    bullpen_or_opener_risk = not starters_ok
    if bullpen_or_opener_risk:
        score -= 0.10
    data_quality = _clamp(score)
    board_status = "FINAL" if data_quality >= 0.80 else ("EARLY" if data_quality >= 0.50 else "LOW_CONFIDENCE")
    return {
        "lineups_confirmed": lineups_confirmed,
        "starters_confirmed_or_probable": starters_ok,
        "weather_available": weather_available,
        "bullpen_or_opener_risk": bullpen_or_opener_risk,
        "data_quality_score": data_quality,
        "board_status": board_status,
        "warnings": warnings,
        "reasons": ["Certainty score reflects data completeness."],
    }
