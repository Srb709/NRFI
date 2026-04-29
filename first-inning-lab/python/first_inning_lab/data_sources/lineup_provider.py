from __future__ import annotations

from first_inning_lab.data_sources.mlb_stats_api import get_boxscore, get_game_feed


def _parse_teams(teams: dict) -> tuple[list, list, dict]:
    diag = {"away_players_seen": 0, "home_players_seen": 0, "away_batting_order_count": 0, "home_batting_order_count": 0}

    def _top(side: str):
        players = (teams.get(side) or {}).get("players") or {}
        diag[f"{side}_players_seen"] = len(players)
        hitters = []
        for p in players.values():
            bo = (p.get("battingOrder") or "").strip()
            if not bo:
                continue
            try:
                order = int(bo[:3])
            except Exception:
                continue
            hitters.append({"order": order, "id": p.get("person", {}).get("id"), "name": p.get("person", {}).get("fullName"), "handedness": (p.get("batSide") or {}).get("code")})
        hitters.sort(key=lambda x: x["order"])
        diag[f"{side}_batting_order_count"] = len(hitters)
        return hitters[:4]

    return _top("away"), _top("home"), diag


def get_lineup_data(game_pk: int | str) -> dict:
    warnings = []
    feed = get_game_feed(game_pk)
    box = get_boxscore(game_pk)
    feed_teams = ((feed.get("liveData") or {}).get("boxscore") or {}).get("teams") or {}
    box_teams = (box.get("teams") or {})

    feed_available = bool(feed_teams)
    boxscore_available = bool(box_teams)
    if not feed_available:
        warnings.append("MLB live feed unavailable for lineup check.")
    away, home, diag = _parse_teams(feed_teams if feed_available else {})
    source = "feed_live"
    if len(away) < 3 or len(home) < 3:
        if not boxscore_available:
            warnings.append("MLB boxscore unavailable for lineup check.")
        else:
            away2, home2, diag2 = _parse_teams(box_teams)
            if len(away2) >= len(away):
                away = away2
            if len(home2) >= len(home):
                home = home2
            for k,v in diag2.items():
                diag[k] = max(diag[k], v)
            source = "boxscore"

    if (diag["away_players_seen"] > 0 or diag["home_players_seen"] > 0) and (diag["away_batting_order_count"] == 0 or diag["home_batting_order_count"] == 0):
        warnings.append("Players found but batting order unavailable; lineups likely not posted.")

    confirmed = len(away) >= 3 and len(home) >= 3
    if not confirmed:
        warnings.append("Lineups unconfirmed; early board only.")
    return {"lineups_confirmed": confirmed, "away_top_order": away, "home_top_order": home, "source": source if (feed_available or boxscore_available) else "unavailable", "diagnostics": {"feed_available": feed_available, "boxscore_available": boxscore_available, **diag}, "warnings": warnings}
