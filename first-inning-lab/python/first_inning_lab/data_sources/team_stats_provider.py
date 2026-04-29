from __future__ import annotations

from pathlib import Path
from typing import Any

from first_inning_lab.data_sources.pybaseball_loader import get_batting_stats_for_season
from first_inning_lab.storage.json_store import atomic_write_json, read_json


def _cache_path(season: int) -> Path:
    return Path(__file__).resolve().parents[3] / f"data/cache/team_stats/team_offense_{season}.json"


def _to_float(v):
    try:
        return float(v)
    except Exception:
        return None


def _load_rows(season: int) -> list[dict[str, Any]]:
    path = _cache_path(season)
    cached = read_json(path, default=None)
    if isinstance(cached, list) and cached:
        return cached
    rows = get_batting_stats_for_season(season)
    out = rows.to_dict(orient="records") if hasattr(rows, "to_dict") else (rows if isinstance(rows, list) else [])
    if out:
        atomic_write_json(path, out)
    return out


def get_team_offense_stats(team_name: str | None, season: int) -> dict[str, Any]:
    payload = {
        "available": False,
        "source": "unavailable",
        "sample_size": {"games": None, "plate_appearances": None},
        "features": {"runs_per_game": None, "obp": None, "slg": None, "ops": None, "woba": None, "wrc_plus": None, "k_rate": None, "bb_rate": None, "first_inning_runs_rate": None},
        "warnings": [],
    }
    rows = _load_rows(season)
    if not rows or not team_name:
        payload["warnings"].append("Team offense stats unavailable; model price withheld.")
        return payload

    row = next((r for r in rows if str(r.get("Team", "")).strip().lower() == team_name.strip().lower()), None)
    if row is None:
        payload["warnings"].append("Team offense stats unavailable; model price withheld.")
        return payload

    g = _to_float(row.get("G"))
    runs = _to_float(row.get("R"))
    payload["available"] = True
    payload["source"] = "pybaseball_batting_stats"
    payload["sample_size"] = {"games": g, "plate_appearances": _to_float(row.get("PA"))}
    payload["features"] = {
        "runs_per_game": None if g in (None, 0) or runs is None else runs / g,
        "obp": _to_float(row.get("OBP")),
        "slg": _to_float(row.get("SLG")),
        "ops": _to_float(row.get("OPS")),
        "woba": _to_float(row.get("wOBA")),
        "wrc_plus": _to_float(row.get("wRC+")),
        "k_rate": None if _to_float(row.get("K%")) is None else _to_float(row.get("K%")) / 100.0,
        "bb_rate": None if _to_float(row.get("BB%")) is None else _to_float(row.get("BB%")) / 100.0,
        "first_inning_runs_rate": None,
    }
    return payload
