from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
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

    history_dir = _root() / "data/history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_json = history_dir / "model_pick_history.json"
    existing = read_json(history_json, default=[]) or []
    by_key = {(x.get("date"), x.get("game_id"), x.get("board_type")): x for x in existing}
    now = datetime.now(timezone.utc).isoformat()
    for game in games:
        pred = predictions.get(game.get("game_id"), {})
        result = next((r for r in results if r.get("game_id") == game.get("game_id")), {})
        row = {
            "date": date,
            "game_id": game.get("game_id"),
            "teams": f"{game.get('away_team')} @ {game.get('home_team')}",
            "model_lean": pred.get("lean"),
            "nrfi_probability": pred.get("nrfi_probability"),
            "confidence": pred.get("confidence_tier"),
            "data_quality": pred.get("data_quality_score"),
            "board_type": pred.get("probability_quality") or "early_board",
            "actual_first_inning_result": result.get("result"),
            "outcome": result.get("outcome"),
            "generated_at": board.get("generated_at"),
            "graded_at": now,
        }
        by_key[(row["date"], row["game_id"], row["board_type"])] = row
    merged = list(by_key.values())
    atomic_write_json(history_json, merged)
    fields = ["date", "game_id", "teams", "model_lean", "nrfi_probability", "confidence", "data_quality", "board_type", "actual_first_inning_result", "outcome", "generated_at", "graded_at"]
    with (history_dir / "model_pick_history.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(merged)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args()
    run(args.date or today_et())
