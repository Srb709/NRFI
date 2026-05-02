from __future__ import annotations

import csv
from pathlib import Path

LEAGUE_MIN_GAMES = 100
VENUE_MIN_GAMES = 20
TEAM_MIN_GAMES = 20
PITCHER_MIN_STARTS = 5


def _dataset_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data/historical/first_inning_results.csv"


def _load_rows() -> tuple[list[dict], list[str]]:
    path = _dataset_path()
    if not path.exists():
        return [], ["Historical first-inning dataset unavailable."]
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh)), []


def _rows_for_season(rows: list[dict], season: int | None) -> list[dict]:
    if season is None:
        return rows
    return [r for r in rows if int(r.get("season") or 0) == season]


def _safe_rate(num: float, den: int) -> float | None:
    return (num / den) if den else None


def _with_season_meta(payload: dict, requested_season: int | None, used_season: int | None, fallback_used: bool) -> dict:
    payload["requested_season"] = requested_season
    payload["used_season"] = used_season
    payload["season_fallback_used"] = fallback_used
    return payload


def _select_rows_for_threshold(rows: list[dict], requested_season: int | None, min_size: int) -> tuple[list[dict], int | None, bool, list[str]]:
    if requested_season is None:
        return rows, None, False, []

    requested_rows = _rows_for_season(rows, requested_season)
    if len(requested_rows) >= min_size:
        return requested_rows, requested_season, False, []

    available_seasons = sorted({int(r.get("season") or 0) for r in rows if (r.get("season") or "").strip() != ""})
    prior_seasons = [s for s in available_seasons if s < requested_season]
    for prior in reversed(prior_seasons):
        prior_rows = _rows_for_season(rows, prior)
        if len(prior_rows) >= min_size:
            return prior_rows, prior, True, [f"Using prior historical season {prior} for {requested_season} board."]

    if requested_rows:
        return requested_rows, requested_season, False, []
    return [], requested_season, False, []


def _select_entity_rows_for_threshold(
    rows: list[dict],
    requested_season: int | None,
    min_size: int,
    entity_label: str,
    entity_filter,
) -> tuple[list[dict], int | None, bool, list[str]]:
    if requested_season is None:
        entity_rows = [r for r in rows if entity_filter(r)]
        return entity_rows, None, False, []

    requested_entity_rows = [r for r in _rows_for_season(rows, requested_season) if entity_filter(r)]
    if len(requested_entity_rows) >= min_size:
        return requested_entity_rows, requested_season, False, []

    available_seasons = sorted({int(r.get("season") or 0) for r in rows if (r.get("season") or "").strip() != ""})
    prior_seasons = [s for s in available_seasons if s < requested_season]
    for prior in reversed(prior_seasons):
        prior_entity_rows = [r for r in _rows_for_season(rows, prior) if entity_filter(r)]
        if len(prior_entity_rows) >= min_size:
            return prior_entity_rows, prior, True, [f"Using prior historical season {prior} for {requested_season} {entity_label} factor."]

    if requested_entity_rows:
        return requested_entity_rows, requested_season, False, []
    return [], requested_season, False, []


def get_league_first_inning_baseline(season: int | None = None) -> dict:
    rows, warnings = _load_rows()
    rows, used_season, fallback_used, season_warnings = _select_rows_for_threshold(rows, season, LEAGUE_MIN_GAMES)
    n = len(rows)
    if n < LEAGUE_MIN_GAMES:
        return _with_season_meta({"available": False, "sample_size": n, "league_avg_first_inning_runs": None, "league_nrfi_rate": None, "league_yrfi_rate": None, "warnings": warnings + season_warnings + ["Historical first-inning sample below threshold."]}, season, used_season, fallback_used)
    total = sum(float(r.get("total_runs_1st") or 0) for r in rows)
    nrfi = sum(1 for r in rows if str(r.get("nrfi_result")).lower() == "true")
    return _with_season_meta({"available": True, "sample_size": n, "league_avg_first_inning_runs": _safe_rate(total, n), "league_nrfi_rate": _safe_rate(nrfi, n), "league_yrfi_rate": _safe_rate(n - nrfi, n), "warnings": warnings + season_warnings}, season, used_season, fallback_used)


def get_venue_first_inning_factor(venue_id: int, season: int | None = None) -> dict:
    rows, warnings = _load_rows()
    venue_rows, used_season, fallback_used, season_warnings = _select_entity_rows_for_threshold(
        rows, season, VENUE_MIN_GAMES, "venue", lambda r: int(r.get("venue_id") or -1) == int(venue_id)
    )
    n = len(venue_rows)
    league = get_league_first_inning_baseline(season)
    if n < VENUE_MIN_GAMES or not league.get("available"):
        return _with_season_meta({"available": False, "venue_id": venue_id, "sample_size": n, "venue_avg_first_inning_runs": None, "venue_nrfi_rate": None, "venue_yrfi_rate": None, "league_avg_first_inning_runs": league.get("league_avg_first_inning_runs"), "venue_first_inning_run_factor": None, "warnings": warnings + season_warnings + ["Historical first-inning sample below threshold."]}, season, used_season, fallback_used)
    venue_total = sum(float(r.get("total_runs_1st") or 0) for r in venue_rows)
    venue_nrfi = sum(1 for r in venue_rows if str(r.get("nrfi_result")).lower() == "true")
    venue_avg = _safe_rate(venue_total, n)
    lg_avg = league.get("league_avg_first_inning_runs")
    factor = (venue_avg / lg_avg) if venue_avg is not None and lg_avg not in (None, 0) else None
    return _with_season_meta({"available": factor is not None, "venue_id": venue_id, "sample_size": n, "venue_avg_first_inning_runs": venue_avg, "venue_nrfi_rate": _safe_rate(venue_nrfi, n), "venue_yrfi_rate": _safe_rate(n - venue_nrfi, n), "league_avg_first_inning_runs": lg_avg, "venue_first_inning_run_factor": factor, "warnings": warnings + season_warnings}, season, used_season, fallback_used)


def get_team_first_inning_profile(team_id: int, season: int | None = None) -> dict:
    rows, warnings = _load_rows()
    games, used_season, fallback_used, season_warnings = _select_entity_rows_for_threshold(
        rows,
        season,
        TEAM_MIN_GAMES,
        "team",
        lambda r: int(r.get("away_team_id") or -1) == team_id or int(r.get("home_team_id") or -1) == team_id,
    )
    n = len(games)
    if n < TEAM_MIN_GAMES:
        return _with_season_meta({"available": False, "team_id": team_id, "sample_size": n, "first_inning_scoring_rate": None, "first_inning_allowed_rate": None, "avg_first_inning_runs_scored": None, "avg_first_inning_runs_allowed": None, "warnings": warnings + season_warnings + ["Historical first-inning sample below threshold."]}, season, used_season, fallback_used)
    scored = allowed = scoring_games = allowed_games = 0
    for r in games:
        if int(r.get("away_team_id") or -1) == team_id:
            s, a = float(r.get("away_runs_1st") or 0), float(r.get("home_runs_1st") or 0)
        else:
            s, a = float(r.get("home_runs_1st") or 0), float(r.get("away_runs_1st") or 0)
        scored += s
        allowed += a
        scoring_games += 1 if s > 0 else 0
        allowed_games += 1 if a > 0 else 0
    return _with_season_meta({"available": True, "team_id": team_id, "sample_size": n, "first_inning_scoring_rate": _safe_rate(scoring_games, n), "first_inning_allowed_rate": _safe_rate(allowed_games, n), "avg_first_inning_runs_scored": _safe_rate(scored, n), "avg_first_inning_runs_allowed": _safe_rate(allowed, n), "warnings": warnings + season_warnings}, season, used_season, fallback_used)


def get_pitcher_first_inning_profile(pitcher_id: int, season: int | None = None) -> dict:
    rows, warnings = _load_rows()
    starts = []
    starts_rows, used_season, fallback_used, season_warnings = _select_entity_rows_for_threshold(
        rows,
        season,
        PITCHER_MIN_STARTS,
        "pitcher",
        lambda r: int(r.get("away_starting_pitcher_id") or -1) == pitcher_id
        or int(r.get("home_starting_pitcher_id") or -1) == pitcher_id,
    )
    for r in starts_rows:
        if int(r.get("away_starting_pitcher_id") or -1) == pitcher_id:
            starts.append(float(r.get("home_runs_1st") or 0))
        if int(r.get("home_starting_pitcher_id") or -1) == pitcher_id:
            starts.append(float(r.get("away_runs_1st") or 0))
    n = len(starts)
    if n < PITCHER_MIN_STARTS:
        return _with_season_meta({"available": False, "pitcher_id": pitcher_id, "sample_size": n, "first_inning_runs_allowed_rate": None, "first_inning_nrfi_rate": None, "avg_first_inning_runs_allowed": None, "warnings": warnings + season_warnings + ["Historical first-inning sample below threshold."]}, season, used_season, fallback_used)
    runs_allowed_games = sum(1 for x in starts if x > 0)
    nrfi_games = sum(1 for x in starts if x == 0)
    return _with_season_meta({"available": True, "pitcher_id": pitcher_id, "sample_size": n, "first_inning_runs_allowed_rate": _safe_rate(runs_allowed_games, n), "first_inning_nrfi_rate": _safe_rate(nrfi_games, n), "avg_first_inning_runs_allowed": _safe_rate(sum(starts), n), "warnings": warnings + season_warnings}, season, used_season, fallback_used)
