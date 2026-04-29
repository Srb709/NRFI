from __future__ import annotations

import argparse
from pathlib import Path

from first_inning_lab.data_sources.mlb_stats_api import get_first_inning_result
from first_inning_lab.storage.json_store import atomic_write_json, read_json
from first_inning_lab.utils.dates import today_et


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def run(date: str):
    live = _root() / "data/live"
    board = read_json(live / "today_board.json", default={}) or {}
    games = board.get("games") or []
    predictions = {p.get("game_id"): p for p in (board.get("predictions") or [])}
    results = []
    for game in games:
        game_pk = game.get("game_pk")
        if game_pk is None:
            result = {"game_pk": -1, "away_runs_1st": None, "home_runs_1st": None, "total_runs_1st": None, "result": "UNKNOWN", "graded": False}
        else:
            result = get_first_inning_result(game_pk)
        lean = predictions.get(game.get("game_id"), {}).get("lean", "PASS")
        if lean == "PASS":
            outcome = "PASS"
        elif result.get("result") in ("UNKNOWN", "PENDING"):
            outcome = "PENDING"
        else:
            outcome = "W" if lean == result.get("result") else "L"
        results.append({"game_id": game.get("game_id"), "lean": lean, "outcome": outcome, **result})
    atomic_write_json(live / "today_results.json", results)
    atomic_write_json(live / "public_record_updates.json", {"date": date, "results": results})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args()
    run(args.date or today_et())
