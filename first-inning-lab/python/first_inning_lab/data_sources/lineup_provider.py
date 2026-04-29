from __future__ import annotations

from first_inning_lab.data_sources.mlb_stats_api import get_game_feed


def get_lineup_data(game_pk: int | str) -> dict:
    out = {"lineups_confirmed": False, "away_top_order": [], "home_top_order": [], "warnings": []}
    feed = get_game_feed(game_pk)
    box = (feed.get("liveData") or {}).get("boxscore") or {}
    teams = box.get("teams") or {}

    def _top(side: str):
        players = (teams.get(side) or {}).get("players") or {}
        hitters = []
        for p in players.values():
            bo = (p.get("battingOrder") or "").strip()
            if not bo:
                continue
            try:
                order = int(bo[:3])
            except Exception:
                continue
            hitters.append({
                "order": order,
                "id": p.get("person", {}).get("id"),
                "name": p.get("person", {}).get("fullName"),
                "handedness": (p.get("batSide") or {}).get("code"),
            })
        hitters.sort(key=lambda x: x["order"])
        return hitters[:4]

    out["away_top_order"] = _top("away")
    out["home_top_order"] = _top("home")
    out["lineups_confirmed"] = len(out["away_top_order"]) >= 3 and len(out["home_top_order"]) >= 3
    if not out["lineups_confirmed"]:
        out["warnings"].append("Lineups unconfirmed; early board only.")
    return out
