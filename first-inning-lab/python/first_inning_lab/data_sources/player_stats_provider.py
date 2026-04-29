from __future__ import annotations

from pathlib import Path
from typing import Any

from first_inning_lab.data_sources.mlb_stats_api import get_player_season_stats
from first_inning_lab.storage.json_store import atomic_write_json, read_json


def _cache_path(pitcher_id: int, season: int) -> Path:
    return Path(__file__).resolve().parents[3] / f"data/cache/player_stats/mlb_pitcher_{pitcher_id}_{season}.json"


def _load(season: int, pitcher_id: int) -> dict[str, Any]:
    path = _cache_path(pitcher_id, season)
    cached = read_json(path, default=None)
    if isinstance(cached, dict) and "available" in cached:
        return cached
    payload = get_player_season_stats(pitcher_id, season, "pitching")
    atomic_write_json(path, payload)
    return payload


def _rate(n, d):
    return None if n is None or d in (None, 0) else float(n) / float(d)


def _from_stats(stats: dict[str, Any], source: str, warnings: list[str]) -> dict[str, Any]:
    bf = stats.get("battersFaced")
    return {
        "available": True,
        "source": source,
        "sample_size": {
            "games": stats.get("gamesPlayed"),
            "innings": stats.get("inningsPitched"),
            "batters_faced": bf,
            "pitches": stats.get("numberOfPitches"),
        },
        "features": {
            "era": stats.get("era"),
            "whip": stats.get("whip"),
            "k_rate": _rate(stats.get("strikeOuts"), bf),
            "bb_rate": _rate(stats.get("baseOnBalls"), bf),
            "hr_rate": _rate(stats.get("homeRuns"), bf),
            "hard_hit_rate": None,
            "barrel_rate": None,
            "xera": None,
            "first_inning_runs_allowed_rate": None,
        },
        "warnings": warnings,
    }


def get_pitcher_stats(pitcher_id: int | None, pitcher_name: str | None, season: int) -> dict[str, Any]:
    if pitcher_id is None:
        return {"available": False, "source": "unavailable", "sample_size": {"games": None, "innings": None, "batters_faced": None, "pitches": None}, "features": {"era": None, "whip": None, "k_rate": None, "bb_rate": None, "hr_rate": None, "hard_hit_rate": None, "barrel_rate": None, "xera": None, "first_inning_runs_allowed_rate": None}, "warnings": ["Pitcher MLB sample unavailable; model price withheld."]}

    current = _load(season, int(pitcher_id))
    cstats = current.get("stats", {}) if current.get("available") else {}
    if cstats and (cstats.get("gamesPlayed") or 0) > 0 and (cstats.get("inningsPitched") or 0) > 0:
        return _from_stats(cstats, "mlb_stats_api_player_pitching", [])

    previous = _load(season - 1, int(pitcher_id))
    pstats = previous.get("stats", {}) if previous.get("available") else {}
    if pstats and (pstats.get("gamesPlayed") or 0) > 0 and (pstats.get("inningsPitched") or 0) > 0:
        return _from_stats(pstats, "mlb_stats_api_player_pitching_previous_season", ["Current-season pitcher sample unavailable; previous-season MLB sample used."])

    return {"available": False, "source": "unavailable", "sample_size": {"games": None, "innings": None, "batters_faced": None, "pitches": None}, "features": {"era": None, "whip": None, "k_rate": None, "bb_rate": None, "hr_rate": None, "hard_hit_rate": None, "barrel_rate": None, "xera": None, "first_inning_runs_allowed_rate": None}, "warnings": ["Pitcher MLB sample unavailable; model price withheld."]}
