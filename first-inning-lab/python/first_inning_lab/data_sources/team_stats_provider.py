from __future__ import annotations

from pathlib import Path
from typing import Any

from first_inning_lab.data_sources.mlb_stats_api import get_team_season_stats
from first_inning_lab.storage.json_store import atomic_write_json, read_json


def _cache_path(team_id: int, season: int) -> Path:
    return Path(__file__).resolve().parents[3] / f"data/cache/team_stats/mlb_team_hitting_{team_id}_{season}.json"


def _load(team_id: int, season: int) -> dict[str, Any]:
    path = _cache_path(team_id, season)
    cached = read_json(path, default=None)
    if isinstance(cached, dict) and "available" in cached:
        return cached
    payload = get_team_season_stats(team_id, season, "hitting")
    atomic_write_json(path, payload)
    return payload


def _rate(n, d):
    return None if n is None or d in (None, 0) else float(n) / float(d)


def _from_stats(stats: dict[str, Any], source: str, warnings: list[str]) -> dict[str, Any]:
    pa = stats.get("plateAppearances")
    g = stats.get("gamesPlayed")
    return {
        "available": True,
        "source": source,
        "sample_size": {"games": g, "plate_appearances": pa},
        "features": {
            "runs_per_game": _rate(stats.get("runs"), g),
            "obp": stats.get("obp"),
            "slg": stats.get("slg"),
            "ops": stats.get("ops"),
            "woba": None,
            "wrc_plus": None,
            "k_rate": _rate(stats.get("strikeOuts"), pa),
            "bb_rate": _rate(stats.get("baseOnBalls"), pa),
            "first_inning_runs_rate": None,
        },
        "warnings": warnings,
    }


def get_team_offense_stats(team_id: int | None, team_name: str | None, season: int) -> dict[str, Any]:
    if team_id is None:
        return {"available": False, "source": "unavailable", "sample_size": {"games": None, "plate_appearances": None}, "features": {"runs_per_game": None, "obp": None, "slg": None, "ops": None, "woba": None, "wrc_plus": None, "k_rate": None, "bb_rate": None, "first_inning_runs_rate": None}, "warnings": ["Team offense MLB sample unavailable; model price withheld."]}
    current = _load(int(team_id), season)
    cstats = current.get("stats", {}) if current.get("available") else {}
    if cstats and (cstats.get("gamesPlayed") or 0) > 0 and (cstats.get("plateAppearances") or 0) > 0:
        return _from_stats(cstats, "mlb_stats_api_team_hitting", [])

    previous = _load(int(team_id), season - 1)
    pstats = previous.get("stats", {}) if previous.get("available") else {}
    if pstats and (pstats.get("gamesPlayed") or 0) > 0 and (pstats.get("plateAppearances") or 0) > 0:
        return _from_stats(pstats, "mlb_stats_api_team_hitting_previous_season", ["Current-season team offense sample unavailable; previous-season MLB sample used."])

    return {"available": False, "source": "unavailable", "sample_size": {"games": None, "plate_appearances": None}, "features": {"runs_per_game": None, "obp": None, "slg": None, "ops": None, "woba": None, "wrc_plus": None, "k_rate": None, "bb_rate": None, "first_inning_runs_rate": None}, "warnings": ["Team offense MLB sample unavailable; model price withheld."]}
