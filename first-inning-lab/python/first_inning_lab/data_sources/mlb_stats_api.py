from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://statsapi.mlb.com/api/v1"
USER_AGENT = "FirstInningLab/1.0 (+free-local-engine)"


def safe_get_json(url: str, timeout: int = 15) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as response:  # nosec B310
            payload = response.read().decode("utf-8")
            data = json.loads(payload)
            return data if isinstance(data, dict) else {}
    except (TimeoutError, HTTPError, URLError, json.JSONDecodeError, ValueError):
        return {}


def _build_url(path: str, params: dict[str, Any] | None = None) -> str:
    query = urlencode({k: v for k, v in (params or {}).items() if v is not None})
    return f"{BASE}{path}" + (f"?{query}" if query else "")


def normalize_game(raw_game: dict[str, Any]) -> dict[str, Any]:
    teams = raw_game.get("teams", {})
    away = teams.get("away", {})
    home = teams.get("home", {})
    away_team = away.get("team", {}).get("name")
    home_team = home.get("team", {}).get("name")
    away_probable_pitcher = away.get("probablePitcher", {}).get("fullName")
    home_probable_pitcher = home.get("probablePitcher", {}).get("fullName")
    return {
        "game_id": str(raw_game.get("gamePk", "")),
        "game_pk": raw_game.get("gamePk"),
        "game_date": (raw_game.get("gameDate") or "")[:10],
        "start_time": raw_game.get("gameDate"),
        "away_team": away_team,
        "home_team": home_team,
        "game": f"{away_team or 'Away'} @ {home_team or 'Home'}",
        "away_team_id": away.get("team", {}).get("id"),
        "home_team_id": home.get("team", {}).get("id"),
        "venue": raw_game.get("venue", {}).get("name"),
        "venue_id": raw_game.get("venue", {}).get("id"),
        "status": raw_game.get("status", {}).get("detailedState", "Unknown"),
        "away_probable_pitcher": away_probable_pitcher,
        "home_probable_pitcher": home_probable_pitcher,
        "away_pitcher": away_probable_pitcher or "TBD",
        "home_pitcher": home_probable_pitcher or "TBD",
        "away_probable_pitcher_id": away.get("probablePitcher", {}).get("id"),
        "home_probable_pitcher_id": home.get("probablePitcher", {}).get("id"),
        "source": "mlb_stats_api",
    }


def get_schedule(date: str) -> list[dict[str, Any]]:
    url = _build_url("/schedule", {"sportId": 1, "date": date, "hydrate": "probablePitcher,venue"})
    schedule = safe_get_json(url)
    out: list[dict[str, Any]] = []
    for date_block in schedule.get("dates", []) or []:
        for game in date_block.get("games", []) or []:
            out.append(normalize_game(game))
    return out


def get_game_feed(game_pk: int | str) -> dict[str, Any]:
    return safe_get_json(_build_url(f"/game/{game_pk}/feed/live"))


def get_linescore(game_pk: int | str) -> dict[str, Any]:
    return safe_get_json(_build_url(f"/game/{game_pk}/linescore"))


def get_boxscore(game_pk: int | str) -> dict[str, Any]:
    return safe_get_json(_build_url(f"/game/{game_pk}/boxscore"))


def get_first_inning_result(game_pk: int | str) -> dict[str, Any]:
    linescore = get_linescore(game_pk)
    innings = linescore.get("innings") or []
    result = {
        "game_pk": int(game_pk),
        "away_runs_1st": None,
        "home_runs_1st": None,
        "total_runs_1st": None,
        "result": "UNKNOWN",
        "graded": False,
    }
    if not innings:
        return result
    first = innings[0] if isinstance(innings[0], dict) else {}
    away = first.get("away", {}).get("runs")
    home = first.get("home", {}).get("runs")
    result["away_runs_1st"] = away
    result["home_runs_1st"] = home
    if away is None or home is None:
        result["result"] = "PENDING"
        return result
    total = int(away) + int(home)
    result["total_runs_1st"] = total
    result["result"] = "NRFI" if total == 0 else "YRFI"
    result["graded"] = True
    return result
