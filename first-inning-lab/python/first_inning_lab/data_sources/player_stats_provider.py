from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from first_inning_lab.data_sources.pybaseball_loader import get_pitching_stats_for_season
from first_inning_lab.storage.json_store import atomic_write_json, read_json


def _cache_path(season: int) -> Path:
    return Path(__file__).resolve().parents[3] / f"data/cache/player_stats/pitchers_{season}.json"


def _load_rows(season: int) -> list[dict[str, Any]]:
    path = _cache_path(season)
    cached = read_json(path, default=None)
    if isinstance(cached, list) and cached:
        return cached
    rows = get_pitching_stats_for_season(season)
    out = rows.to_dict(orient="records") if hasattr(rows, "to_dict") else (rows if isinstance(rows, list) else [])
    if out:
        atomic_write_json(path, out)
    return out


def _to_float(v):
    try:
        return float(v)
    except Exception:
        return None


def get_pitcher_stats(pitcher_id: int | None, pitcher_name: str | None, season: int) -> dict[str, Any]:
    payload = {
        "available": False,
        "source": "unavailable",
        "sample_size": {"games": None, "innings": None, "batters_faced": None, "pitches": None},
        "features": {"era": None, "whip": None, "k_rate": None, "bb_rate": None, "hr_rate": None, "hard_hit_rate": None, "barrel_rate": None, "xera": None, "first_inning_runs_allowed_rate": None},
        "warnings": [],
    }
    rows = _load_rows(season)
    if not rows:
        payload["warnings"].append("Pitcher current-season sample unavailable.")
        return payload

    row = None
    if pitcher_id is not None:
        for r in rows:
            if int(r.get("IDfg") or -1) == int(pitcher_id):
                row = r
                break
    if row is None and pitcher_name:
        n = pitcher_name.strip().lower()
        for r in rows:
            if str(r.get("Name", "")).strip().lower() == n:
                row = r
                break

    if row is None:
        payload["warnings"].append("Pitcher current-season sample unavailable.")
        return payload

    ip = _to_float(row.get("IP"))
    bf = _to_float(row.get("BF"))
    hr = _to_float(row.get("HR"))
    bb_pct = _to_float(row.get("BB%"))
    k_pct = _to_float(row.get("K%"))
    payload["available"] = True
    payload["source"] = "pybaseball_pitching_stats"
    payload["sample_size"] = {
        "games": _to_float(row.get("G")),
        "innings": ip,
        "batters_faced": bf,
        "pitches": None,
    }
    payload["features"] = {
        "era": _to_float(row.get("ERA")),
        "whip": _to_float(row.get("WHIP")),
        "k_rate": None if k_pct is None else k_pct / 100.0,
        "bb_rate": None if bb_pct is None else bb_pct / 100.0,
        "hr_rate": None if (hr is None or bf in (None, 0)) else hr / bf,
        "hard_hit_rate": None,
        "barrel_rate": None,
        "xera": _to_float(row.get("xERA")),
        "first_inning_runs_allowed_rate": None,
    }
    return payload
