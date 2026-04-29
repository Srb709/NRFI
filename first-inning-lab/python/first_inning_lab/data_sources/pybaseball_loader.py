from __future__ import annotations

import importlib.util


def dependency_available(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None


def _safe_pybaseball_call(callable_name: str, *args, **kwargs):
    if not dependency_available("pybaseball"):
        return []
    try:
        import pybaseball as pb

        fn = getattr(pb, callable_name)
        return fn(*args, **kwargs)
    except Exception:
        return []


def get_pitching_stats_for_season(season: int):
    return _safe_pybaseball_call("pitching_stats", season)


def get_batting_stats_for_season(season: int):
    return _safe_pybaseball_call("batting_stats", season)
