from __future__ import annotations

import importlib.util
from pathlib import Path


def dependency_available(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None


def _empty_rows() -> list[dict]:
    return []


def _cache_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "processed" / "cache" / f"{name}.csv"


def _maybe_cache(name: str, rows, use_cache: bool):
    if not use_cache:
        return
    cache = _cache_path(name)
    cache.parent.mkdir(parents=True, exist_ok=True)
    try:
        if dependency_available("pandas"):
            import pandas as pd

            if isinstance(rows, pd.DataFrame):
                rows.to_csv(cache, index=False)
            else:
                pd.DataFrame(rows).to_csv(cache, index=False)
    except Exception:
        return


def _safe_pybaseball_call(callable_name: str, *args, use_cache: bool = False, cache_key: str | None = None, **kwargs):
    if not dependency_available("pybaseball"):
        return _empty_rows()
    try:
        import pybaseball as pb

        fn = getattr(pb, callable_name)
        result = fn(*args, **kwargs)
        _maybe_cache(cache_key or callable_name, result, use_cache)
        return result if result is not None else _empty_rows()
    except Exception:
        return _empty_rows()


def get_pitching_stats_for_season(season: int):
    return _safe_pybaseball_call("pitching_stats", season, use_cache=True, cache_key=f"pitching_{season}")


def get_batting_stats_for_season(season: int):
    return _safe_pybaseball_call("batting_stats", season, use_cache=True, cache_key=f"batting_{season}")


def get_statcast_range(start_date: str, end_date: str):
    return _safe_pybaseball_call("statcast", start_date, end_date, use_cache=True, cache_key=f"statcast_{start_date}_{end_date}")


def get_pitcher_statcast(player_id: int, start_date: str, end_date: str):
    return _safe_pybaseball_call("statcast_pitcher", start_date, end_date, player_id, use_cache=True, cache_key=f"pitcher_{player_id}_{start_date}_{end_date}")


def get_batter_statcast(player_id: int, start_date: str, end_date: str):
    return _safe_pybaseball_call("statcast_batter", start_date, end_date, player_id, use_cache=True, cache_key=f"batter_{player_id}_{start_date}_{end_date}")
