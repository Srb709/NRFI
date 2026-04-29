from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from first_inning_lab.data_sources.mlb_stats_api import get_schedule
from first_inning_lab.data_sources.weather_client import get_game_weather
from first_inning_lab.features.assemble_game_features import assemble_game_features
from first_inning_lab.modeling.baseline_rules_model import predict_baseline
from first_inning_lab.storage.json_store import atomic_write_json, read_json
from first_inning_lab.utils.dates import today_et


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _empty_board(date: str, warnings: list[str]) -> dict:
    return {"generated_at": datetime.utcnow().isoformat() + "Z", "date": date, "source": "free_local_pipeline_fallback", "board_status": "LOW_CONFIDENCE", "games": [], "predictions": [], "warnings": warnings, "summary": {"games": 0, "nrfi_leans": 0, "yrfi_leans": 0, "passes": 0, "low_confidence": 0, "average_data_quality": None}}


def run(date: str):
    warnings: list[str] = []
    games = get_schedule(date)
    if not games:
        warnings.append("Schedule unavailable from MLB API; generated fallback board.")
    parks = {str(p.get("venue_id")): p for p in read_json(_root() / "data/reference/park_factors.json", default=[])}
    preds, statuses = [], []
    for game in games:
        park = parks.get(str(game.get("venue_id")))
        weather = get_game_weather((park or {}).get("latitude"), (park or {}).get("longitude"), game.get("start_time") or "")
        assembled = assemble_game_features(game, int(date[:4]), parks, weather)
        pred = predict_baseline(assembled)
        pred["game_id"] = game.get("game_id")
        pred["board_status"] = "FINAL_BOARD" if assembled["feature_status"].get("lineups_confirmed") else "EARLY_BOARD"
        preds.append(pred)
        statuses.append(pred["board_status"])
    avg_quality = (sum(float(p.get("data_quality_score", 0.5)) for p in preds) / len(preds)) if preds else None
    summary = {"games": len(games), "nrfi_leans": sum(1 for p in preds if p.get("lean") == "NRFI"), "yrfi_leans": sum(1 for p in preds if p.get("lean") == "YRFI"), "passes": sum(1 for p in preds if p.get("lean") == "PASS"), "low_confidence": sum(1 for p in preds if p.get("board_status") == "LOW_CONFIDENCE"), "average_data_quality": avg_quality}
    board = _empty_board(date, warnings) if not games else {"generated_at": datetime.utcnow().isoformat() + "Z", "date": date, "source": "free_local_pipeline", "board_status": "MIXED" if len(set(statuses)) > 1 else (statuses[0] if statuses else "EARLY"), "games": games, "predictions": preds, "warnings": warnings, "summary": summary}
    live = _root() / "data/live"
    atomic_write_json(live / "today_games.json", board["games"])
    atomic_write_json(live / "today_predictions.json", board["predictions"])
    atomic_write_json(live / "today_board.json", board)

    priced = [p for p in preds if p.get("probability_available")]
    miss_pitcher = sum(1 for p in preds if not p.get("feature_status", {}).get("pitcher_stats_available"))
    miss_offense = sum(1 for p in preds if not p.get("feature_status", {}).get("team_offense_stats_available"))
    weather_unavail = sum(1 for p in preds if not p.get("feature_status", {}).get("weather_available"))
    lineup_unconfirmed = sum(1 for p in preds if not p.get("feature_status", {}).get("lineups_confirmed"))
    prev_pitcher = sum(1 for p in preds if any("Current-season pitcher sample unavailable; previous-season MLB sample used." == w for w in p.get("warnings", [])))
    prev_team = sum(1 for p in preds if any("Current-season team offense sample unavailable; previous-season MLB sample used." == w for w in p.get("warnings", [])))

    print("First Inning Lab Board")
    print(f"Date: {date}")
    print(f"Source: {board['source']}")
    print(f"Generated: {board['generated_at']}")
    print(f"Games: {summary['games']}")
    print(f"Priced games: {len(priced)}")
    print(f"Unpriced games: {len(preds) - len(priced)}")
    print(f"Missing pitcher stats: {miss_pitcher}")
    print(f"Missing team offense stats: {miss_offense}")
    print(f"Weather unavailable: {weather_unavail}")
    print(f"Lineups unconfirmed: {lineup_unconfirmed}")
    print(f"Previous-season pitcher samples used: {prev_pitcher}")
    print(f"Previous-season team samples used: {prev_team}")
    print(f"Average data quality: {0 if avg_quality is None else round(avg_quality * 100)}%")

    if priced:
        print("Top board:")
        top = sorted(priced, key=lambda x: x.get("nrfi_probability") or 0, reverse=True)[:5]
        for i, item in enumerate(top, 1):
            gm = next((g for g in games if g.get("game_id") == item.get("game_id")), {})
            print(f"{i}. {gm.get('away_team')} @ {gm.get('home_team')} - {item.get('lean')} - NRFI {round((item.get('nrfi_probability') or 0) * 100)}% - Data quality {round((item.get('data_quality_score') or 0) * 100)}%")
    elif games:
        print("All games are unpriced because required real inputs are missing and pricing is withheld.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args()
    run(args.date or today_et())
