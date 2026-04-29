from __future__ import annotations

from first_inning_lab.data_sources.lineup_provider import get_lineup_data
from first_inning_lab.data_sources.player_stats_provider import get_pitcher_stats
from first_inning_lab.data_sources.team_stats_provider import get_team_offense_stats
from first_inning_lab.features.park_weather_features import build_park_weather_features
from first_inning_lab.features.historical_first_inning_features import get_league_first_inning_baseline, get_pitcher_first_inning_profile, get_team_first_inning_profile, get_venue_first_inning_factor
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
    park_score = park_weather.get("park_weather_score") if park_weather.get("park_factor_available") else None
    historical_venue = get_venue_first_inning_factor(int(game.get("venue_id") or -1), season)
    historical_league = get_league_first_inning_baseline(season)
    historical_team_away = get_team_first_inning_profile(int(game.get("away_team_id") or -1), season)
    historical_team_home = get_team_first_inning_profile(int(game.get("home_team_id") or -1), season)
    historical_pitcher_away = get_pitcher_first_inning_profile(int(game.get("away_probable_pitcher_id") or -1), season)
    historical_pitcher_home = get_pitcher_first_inning_profile(int(game.get("home_probable_pitcher_id") or -1), season)

    pitcher_available = away_p.get("available") and home_p.get("available") and pitch_score_a is not None and pitch_score_h is not None
    offense_available = away_o.get("available") and home_o.get("available") and off_score_a is not None and off_score_h is not None
    historical_venue_ok = bool(historical_venue.get("available") and historical_venue.get("sample_size",0) >= 20 and historical_venue.get("venue_first_inning_run_factor") is not None)
    venue_score = None if not historical_venue_ok else max(0.0, min(1.0, 0.5 + ((historical_venue.get("venue_first_inning_run_factor") - 1.0) * 0.3)))
    park_available = park_score is not None
    park_or_venue_available = park_available or historical_venue_ok
    weather_available = bool((weather or {}).get("available"))

    if not pitcher_available:
        missing.append("pitcher_stats")
        warnings.append("Pitcher stats unavailable; model price withheld.")
    if not offense_available:
        missing.append("team_offense_stats")
        warnings.append("Team offense stats unavailable; model price withheld.")
    if not park_available:
        missing.append("park_factor")
    if not historical_venue_ok:
        missing.append("historical_venue_factor")
    if not park_or_venue_available:
        missing.append("park_or_venue_signal")
        warnings.append("Park/venue signal unavailable; model price withheld.")
    if not weather_available:
        warnings.append("Weather unavailable; weather not included.")

    avail_count = sum([probable, pitcher_available, offense_available, park_or_venue_available, weather_available, lineup.get("lineups_confirmed", False)])
    dq = avail_count / 6.0

    return {
        "game_id": str(game.get("game_id")),
        "feature_status": {
            "probable_pitchers_available": probable,
            "pitcher_stats_available": bool(pitcher_available),
            "team_offense_stats_available": bool(offense_available),
            "park_factor_available": bool(park_available),
            "historical_venue_factor_available": bool(historical_venue_ok),
            "park_or_venue_signal_available": bool(park_or_venue_available),
            "historical_first_inning_available": bool(historical_league.get("available")),
            "stadium_coordinates_available": bool(park_weather.get("stadium_coordinates_available")),
            "weather_available": bool(weather_available),
            "lineups_confirmed": bool(lineup.get("lineups_confirmed")),
        },
        "real_features": {
            "pitcher_safety_score": None if not pitcher_available else (pitch_score_a + pitch_score_h) / 2.0,
            "offense_danger_score": None if not offense_available else (off_score_a + off_score_h) / 2.0,
            "park_weather_score": park_score,
            "venue_first_inning_score": venue_score,
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
            "historical_venue": historical_venue,
            "historical_team_away": historical_team_away,
            "historical_team_home": historical_team_home,
            "historical_pitcher_away": historical_pitcher_away,
            "historical_pitcher_home": historical_pitcher_home,
            "historical_league": historical_league,
        },
        "missing_data": missing,
        "warnings": dedupe_preserve_order(warnings + away_p.get("warnings", []) + home_p.get("warnings", []) + away_o.get("warnings", []) + home_o.get("warnings", []) + lineup.get("warnings", []) + historical_venue.get("warnings", []) + historical_team_away.get("warnings", []) + historical_team_home.get("warnings", []) + historical_pitcher_away.get("warnings", []) + historical_pitcher_home.get("warnings", []) + historical_league.get("warnings", [])),
        "data_quality_score": round(dq, 3),
    }
