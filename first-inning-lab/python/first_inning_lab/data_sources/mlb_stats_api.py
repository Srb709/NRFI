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


def _to_number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        text = str(value)
        return float(text) if "." in text else int(text)
    except Exception:
        return None


def _normalized_split(payload: dict[str, Any]) -> dict[str, Any] | None:
    stats = payload.get("stats") or []
    if stats and isinstance(stats[0], dict):
        splits = stats[0].get("splits") or []
        if splits and isinstance(splits[0], dict):
            return splits[0].get("stat") or {}
    people = payload.get("people") or []
    if people and isinstance(people[0], dict):
        pstats = people[0].get("stats") or []
        if pstats and isinstance(pstats[0], dict):
            splits = pstats[0].get("splits") or []
            if splits and isinstance(splits[0], dict):
                return splits[0].get("stat") or {}
    return None


def _normalize_player_stat(stat: dict[str, Any]) -> dict[str, Any]:
    return {
        "gamesPlayed": _to_number(stat.get("gamesPlayed") or stat.get("games")),
        "gamesStarted": _to_number(stat.get("gamesStarted") or stat.get("gs")),
        "inningsPitched": _to_number(stat.get("inningsPitched") or stat.get("ip")),
        "era": _to_number(stat.get("era")),
        "whip": _to_number(stat.get("whip")),
        "strikeOuts": _to_number(stat.get("strikeOuts") or stat.get("so")),
        "baseOnBalls": _to_number(stat.get("baseOnBalls") or stat.get("bb")),
        "homeRuns": _to_number(stat.get("homeRuns") or stat.get("hr")),
        "battersFaced": _to_number(stat.get("battersFaced") or stat.get("bf")),
        "numberOfPitches": _to_number(stat.get("numberOfPitches") or stat.get("np")),
    }


def _normalize_team_stat(stat: dict[str, Any]) -> dict[str, Any]:
    return {
        "gamesPlayed": _to_number(stat.get("gamesPlayed") or stat.get("g")),
        "runs": _to_number(stat.get("runs") or stat.get("r")),
        "plateAppearances": _to_number(stat.get("plateAppearances") or stat.get("pa")),
        "hits": _to_number(stat.get("hits") or stat.get("h")),
        "doubles": _to_number(stat.get("doubles") or stat.get("2b")),
        "triples": _to_number(stat.get("triples") or stat.get("3b")),
        "homeRuns": _to_number(stat.get("homeRuns") or stat.get("hr")),
        "baseOnBalls": _to_number(stat.get("baseOnBalls") or stat.get("bb")),
        "strikeOuts": _to_number(stat.get("strikeOuts") or stat.get("so")),
        "obp": _to_number(stat.get("obp")),
        "slg": _to_number(stat.get("slg")),
        "ops": _to_number(stat.get("ops")),
    }


def get_player_season_stats(person_id: int, season: int, group: str) -> dict[str, Any]:
    urls = [
        _build_url(f"/people/{person_id}/stats", {"stats": "season", "group": group, "season": season}),
        _build_url(f"/people/{person_id}", {"hydrate": f"stats(group=[{group}],type=[season],season={season})"}),
        _build_url("/stats", {"stats": "season", "group": group, "personId": person_id, "season": season}),
    ]
    for url in urls:
        payload = safe_get_json(url)
        split = _normalized_split(payload)
        if split:
            return {"available": True, "source": "mlb_stats_api", "raw": split, "stats": _normalize_player_stat(split)}
    return {"available": False, "source": "unavailable", "raw": {}, "stats": {}}


def get_team_season_stats(team_id: int, season: int, group: str) -> dict[str, Any]:
    urls = [
        _build_url("/stats", {"stats": "season", "group": group, "teamId": team_id, "season": season}),
        _build_url(f"/teams/{team_id}/stats", {"stats": "season", "group": group, "season": season}),
    ]
    for url in urls:
        payload = safe_get_json(url)
        split = _normalized_split(payload)
        if split:
            return {"available": True, "source": "mlb_stats_api", "raw": split, "stats": _normalize_team_stat(split)}
    return {"available": False, "source": "unavailable", "raw": {}, "stats": {}}


def normalize_game(raw_game: dict[str, Any]) -> dict[str, Any]:
    teams = raw_game.get("teams", {})
    away = teams.get("away", {})
    home = teams.get("home", {})
    away_team = away.get("team", {}).get("name")
    home_team = home.get("team", {}).get("name")
    away_probable_pitcher = away.get("probablePitcher", {}).get("fullName")
    home_probable_pitcher = home.get("probablePitcher", {}).get("fullName")
    return {"game_id": str(raw_game.get("gamePk", "")), "game_pk": raw_game.get("gamePk"), "game_date": (raw_game.get("gameDate") or "")[:10], "start_time": raw_game.get("gameDate"), "away_team": away_team, "home_team": home_team, "game": f"{away_team or 'Away'} @ {home_team or 'Home'}", "away_team_id": away.get("team", {}).get("id"), "home_team_id": home.get("team", {}).get("id"), "venue": raw_game.get("venue", {}).get("name"), "venue_id": raw_game.get("venue", {}).get("id"), "status": raw_game.get("status", {}).get("detailedState", "Unknown"), "away_probable_pitcher": away_probable_pitcher, "home_probable_pitcher": home_probable_pitcher, "away_pitcher": away_probable_pitcher or "TBD", "home_pitcher": home_probable_pitcher or "TBD", "away_probable_pitcher_id": away.get("probablePitcher", {}).get("id"), "home_probable_pitcher_id": home.get("probablePitcher", {}).get("id"), "source": "mlb_stats_api"}


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
    result = {"game_pk": int(game_pk), "away_runs_1st": None, "home_runs_1st": None, "total_runs_1st": None, "result": "UNKNOWN", "graded": False}
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
