from __future__ import annotations

from first_inning_lab.data_sources.lineup_provider import get_lineup_data
from first_inning_lab.data_sources.player_stats_provider import get_pitcher_stats
from first_inning_lab.data_sources.team_stats_provider import get_team_offense_stats
from first_inning_lab.features.park_weather_features import build_park_weather_features
from first_inning_lab.utils.collections import dedupe_preserve_order


def _score_pitcher(p: dict) -> float | None:
    f = p.get("features", {})
    if not p.get("available"):
        return None
    era = f.get("era")
    whip = f.get("whip")
    if era is None or whip is None:
        return None
    return max(0.0, min(1.0, 1.0 - ((era / 8.0) * 0.6 + (whip / 2.0) * 0.4)))


def _score_offense(o: dict) -> float | None:
    f = o.get("features", {})
    if not o.get("available"):
        return None
    ops = f.get("ops")
    rpg = f.get("runs_per_game")
    if ops is None or rpg is None:
        return None
    return max(0.0, min(1.0, ((ops - 0.6) / 0.35) * 0.6 + (rpg / 8.0) * 0.4))


def assemble_game_features(game: dict, season: int, parks: dict, weather: dict) -> dict:
    warnings, missing = [], []
    probable = bool(game.get("away_probable_pitcher")) and bool(game.get("home_probable_pitcher"))
    if not probable:
        missing.append("probable_pitchers")

    away_p = get_pitcher_stats(game.get("away_probable_pitcher_id"), game.get("away_probable_pitcher"), season)
    home_p = get_pitcher_stats(game.get("home_probable_pitcher_id"), game.get("home_probable_pitcher"), season)
    away_o = get_team_offense_stats(game.get("away_team_id"), game.get("away_team"), season)
    home_o = get_team_offense_stats(game.get("home_team_id"), game.get("home_team"), season)
    lineup = get_lineup_data(game.get("game_pk") or game.get("game_id"))
    park_weather = build_park_weather_features(game, parks, weather)

    pitch_score_a, pitch_score_h = _score_pitcher(away_p), _score_pitcher(home_p)
    off_score_a, off_score_h = _score_offense(away_o), _score_offense(home_o)
    park_score = park_weather.get("park_weather_score") if park_weather.get("park_factor_available", True) else None

    pitcher_available = away_p.get("available") and home_p.get("available") and pitch_score_a is not None and pitch_score_h is not None
    offense_available = away_o.get("available") and home_o.get("available") and off_score_a is not None and off_score_h is not None
    park_available = park_score is not None
    weather_available = bool(weather) and weather.get("source") != "neutral_fallback"

    if not pitcher_available:
        missing.append("pitcher_stats")
        warnings.append("Pitcher stats unavailable; model price withheld.")
    if not offense_available:
        missing.append("team_offense_stats")
        warnings.append("Team offense stats unavailable; model price withheld.")
    if not park_available:
        missing.append("park_factor")
        warnings.append("Park factor unavailable; model price withheld.")
    if not weather_available:
        warnings.append("Weather unavailable; weather not included.")

    avail_count = sum([probable, pitcher_available, offense_available, park_available, weather_available, lineup.get("lineups_confirmed", False)])
    dq = avail_count / 6.0

    return {
        "game_id": str(game.get("game_id")),
        "feature_status": {
            "probable_pitchers_available": probable,
            "pitcher_stats_available": bool(pitcher_available),
            "team_offense_stats_available": bool(offense_available),
            "park_factor_available": bool(park_available),
            "weather_available": bool(weather_available),
            "lineups_confirmed": bool(lineup.get("lineups_confirmed")),
        },
        "real_features": {
            "pitcher_safety_score": None if not pitcher_available else (pitch_score_a + pitch_score_h) / 2.0,
            "offense_danger_score": None if not offense_available else (off_score_a + off_score_h) / 2.0,
            "park_weather_score": park_score,
            "recent_form_score": None,
        },
        "raw_features": {
            "away_pitcher": away_p,
            "home_pitcher": home_p,
            "away_offense": away_o,
            "home_offense": home_o,
            "park": park_weather,
            "weather": weather,
            "lineups": lineup,
        },
        "missing_data": missing,
        "warnings": dedupe_preserve_order(warnings + away_p.get("warnings", []) + home_p.get("warnings", []) + away_o.get("warnings", []) + home_o.get("warnings", []) + lineup.get("warnings", [])),
        "data_quality_score": round(dq, 3),
    }
