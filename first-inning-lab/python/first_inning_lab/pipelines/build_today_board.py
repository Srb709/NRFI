from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from first_inning_lab.data_sources.mlb_stats_api import get_schedule
from first_inning_lab.data_sources.weather_client import get_game_weather
from first_inning_lab.features.certainty_features import build_certainty_features
from first_inning_lab.features.matchup_features import combine_game_features
from first_inning_lab.features.offense_features import build_offense_features
from first_inning_lab.features.park_weather_features import build_park_weather_features
from first_inning_lab.features.pitcher_features import build_pitcher_features
from first_inning_lab.modeling.baseline_rules_model import predict_baseline
from first_inning_lab.storage.json_store import atomic_write_json, read_json
from first_inning_lab.utils.dates import today_et


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _empty_board(date: str, warnings: list[str]) -> dict:
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "date": date,
        "source": "free_local_pipeline_fallback",
        "board_status": "LOW_CONFIDENCE",
        "games": [],
        "predictions": [],
        "warnings": warnings,
        "summary": {"games": 0, "nrfi_leans": 0, "yrfi_leans": 0, "passes": 0, "low_confidence": 0, "average_data_quality": None},
    }


def run(date: str):
    warnings: list[str] = []
    try:
        games = get_schedule(date)
    except Exception:
        games = []
    if not games:
        warnings.append("Schedule unavailable from MLB API; generated fallback board.")
    parks = {str(p.get("venue_id")): p for p in read_json(_root() / "data/reference/park_factors.json", default=[])}
    preds = []
    statuses = []
    for game in games:
        park = parks.get(str(game.get("venue_id")))
        weather = get_game_weather((park or {}).get("latitude"), (park or {}).get("longitude"), game.get("start_time") or "")
        away_pitcher = build_pitcher_features(game.get("away_probable_pitcher_id"), game.get("away_probable_pitcher"), int(date[:4]), date)
        home_pitcher = build_pitcher_features(game.get("home_probable_pitcher_id"), game.get("home_probable_pitcher"), int(date[:4]), date)
        away_offense = build_offense_features(game.get("away_team_id"), game.get("away_team") or "Unknown", None, None, int(date[:4]), date)
        home_offense = build_offense_features(game.get("home_team_id"), game.get("home_team") or "Unknown", None, None, int(date[:4]), date)
        park_weather = build_park_weather_features(game, parks, weather)
        certainty = build_certainty_features(game, away_pitcher, home_pitcher, away_offense, home_offense, weather)
        matchup = combine_game_features(game, away_pitcher, home_pitcher, away_offense, home_offense, park_weather, certainty)
        pred = predict_baseline(matchup)
        pred["game_id"] = game.get("game_id")
        pred["board_status"] = certainty.get("board_status")
        preds.append(pred)
        statuses.append(certainty.get("board_status"))
    avg_quality = (sum(float(p.get("data_quality_score", 0.5)) for p in preds) / len(preds)) if preds else None
    summary = {
        "games": len(games),
        "nrfi_leans": sum(1 for p in preds if p.get("lean") == "NRFI"),
        "yrfi_leans": sum(1 for p in preds if p.get("lean") == "YRFI"),
        "passes": sum(1 for p in preds if p.get("lean") == "PASS"),
        "low_confidence": sum(1 for p in preds if p.get("board_status") == "LOW_CONFIDENCE"),
        "average_data_quality": avg_quality,
    }
    board = _empty_board(date, warnings) if not games else {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "date": date,
        "source": "free_local_pipeline",
        "board_status": "MIXED" if len(set(statuses)) > 1 else (statuses[0] if statuses else "EARLY"),
        "games": games,
        "predictions": preds,
        "warnings": warnings,
        "summary": summary,
    }
    live = _root() / "data/live"
    atomic_write_json(live / "today_games.json", board["games"])
    atomic_write_json(live / "today_predictions.json", board["predictions"])
    atomic_write_json(live / "today_board.json", board)
    print("First Inning Lab Board")
    print(f"Date: {date}")
    print(f"Source: {board['source']}")
    print(f"Generated: {board['generated_at']}")
    print(f"Games: {summary['games']}")
    print(f"NRFI: {summary['nrfi_leans']}")
    print(f"YRFI: {summary['yrfi_leans']}")
    print(f"PASS: {summary['passes']}")
    print(f"Low confidence: {summary['low_confidence']}")
    if not games:
        print("No games available from schedule pull; wrote fallback live files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args()
    run(args.date or today_et())
