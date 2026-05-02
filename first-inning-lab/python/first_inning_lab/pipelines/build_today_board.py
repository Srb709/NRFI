from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from first_inning_lab.data_sources.mlb_stats_api import get_schedule
from first_inning_lab.data_sources.weather_client import get_game_weather
from first_inning_lab.features.assemble_game_features import assemble_game_features
from first_inning_lab.modeling.baseline_rules_model import predict_baseline
from first_inning_lab.storage.json_store import atomic_write_json, read_json
from first_inning_lab.utils.dates import today_et


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def run(date: str, backtest: bool = False):
    warnings: list[str] = []
    games = get_schedule(date)
    parks = {str(p.get("venue_id")): p for p in read_json(_root() / "data/reference/park_factors.json", default=[])}
    preds = []
    for game in games:
        park = parks.get(str(game.get("venue_id")))
        weather = get_game_weather((park or {}).get("latitude"), (park or {}).get("longitude"), game.get("start_time") or "")
        historical_season = int((datetime.fromisoformat(date) - timedelta(days=1)).strftime("%Y")) if not backtest else int(date[:4])
        assembled = assemble_game_features(game, historical_season, parks, weather)
        pred = predict_baseline(assembled)
        pred["game_id"] = game.get("game_id")
        pred["board_status"] = "FINAL_BOARD" if assembled["feature_status"].get("lineups_confirmed") else "EARLY_BOARD"
        pred["raw_features"] = assembled.get("raw_features", {})
        preds.append(pred)

    live = _root() / "data/live"
    atomic_write_json(live / "today_games.json", games)
    atomic_write_json(live / "today_predictions.json", preds)
    avg_quality = (sum(float(p.get("data_quality_score", 0.0)) for p in preds) / len(preds)) if preds else None
    summary = {"games": len(games), "average_data_quality": avg_quality}
    atomic_write_json(live / "today_board.json", {"generated_at": datetime.now(timezone.utc).isoformat(), "date": date, "source": "free_local_pipeline", "board_status": "LOW_CONFIDENCE" if not games else "MIXED", "games": games, "predictions": preds, "warnings": warnings, "summary": summary})

    priced = [p for p in preds if p.get("probability_available")]
    fs = [p.get("feature_status", {}) for p in preds]
    print("First Inning Lab Board")
    print(f"Date: {date}")
    print(f"Games: {len(games)}")
    print(f"Priced games: {len(priced)}")
    print(f"Early-board priced games: {sum(1 for p in preds if p.get('pricing_readiness') == 'priced_core_early')}")
    print(f"Final-board priced games: {sum(1 for p in preds if p.get('pricing_readiness') == 'priced_final_lineup_confirmed')}")
    print(f"Unpriced games: {len(preds)-len(priced)}")
    print(f"Missing probable pitchers: {sum(1 for x in fs if not x.get('probable_pitchers_available'))}")
    print(f"Missing pitcher stats: {sum(1 for x in fs if not x.get('pitcher_stats_available'))}")
    print(f"Missing team offense stats: {sum(1 for x in fs if not x.get('team_offense_stats_available'))}")
    print(f"Missing static park factor: {sum(1 for x in fs if not x.get('park_factor_available'))}")
    print(f"Missing historical venue factor: {sum(1 for x in fs if not x.get('historical_venue_factor_available'))}")
    print(f"Missing park/venue signal: {sum(1 for x in fs if not x.get('park_or_venue_signal_available'))}")
    print(f"Weather unavailable: {sum(1 for x in fs if not x.get('weather_available'))}")
    print(f"Lineups unconfirmed: {sum(1 for x in fs if not x.get('lineups_confirmed'))}")
    historical_rows = [p.get("raw_features", {}).get("historical_league", {}) for p in preds]
    hist_dataset_missing = sum(1 for h in historical_rows if "Historical first-inning dataset unavailable." in (h.get("warnings") or []))
    hist_below_threshold = sum(1 for h in historical_rows if h and not h.get("available") and "Historical first-inning dataset unavailable." not in (h.get("warnings") or []))
    fallback_keys = {
        "league": "historical_league",
        "venue": "historical_venue",
        "team_away": "historical_team_away",
        "team_home": "historical_team_home",
        "pitcher_away": "historical_pitcher_away",
        "pitcher_home": "historical_pitcher_home",
    }
    hist_fallback_detail = {k: 0 for k in fallback_keys}
    hist_fallback_used = 0
    for pred in preds:
        raw = pred.get("raw_features", {})
        used_any = False
        for label, key in fallback_keys.items():
            block = raw.get(key, {})
            if block.get("season_fallback_used"):
                hist_fallback_detail[label] += 1
                used_any = True
        if used_any:
            hist_fallback_used += 1
    hist_missing = sum(1 for x in fs if not x.get('historical_first_inning_available'))
    print(f"Historical first-inning unavailable (all causes): {hist_missing}")
    print(f"Historical dataset file missing: {hist_dataset_missing}")
    print(f"Historical dataset below threshold: {hist_below_threshold}")
    print(f"Historical prior-season fallback used: {hist_fallback_used}")
    print(f"Historical fallback detail: {hist_fallback_detail}")
    if hist_dataset_missing:
        print("Historical first-inning dataset file missing; run build_historical_first_inning_dataset.")
    print(f"Average data quality: {0 if avg_quality is None else round(avg_quality * 100)}%")

    if priced:
        for i, item in enumerate(priced[:5], 1):
            gm = next((g for g in games if g.get("game_id") == item.get("game_id")), {})
            source = "historical venue" if item.get("feature_status", {}).get("historical_venue_factor_available") else "static park"
            print(f"{i}. {gm.get('away_team')} @ {gm.get('home_team')} - {item.get('lean')} - NRFI {round((item.get('nrfi_probability') or 0) * 100)}% - Quality {round((item.get('data_quality_score') or 0) * 100)}% - {'early_board' if item.get('pricing_readiness')=='priced_core_early' else 'final_board'} - {source}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--date"); parser.add_argument("--backtest", action="store_true"); args = parser.parse_args(); run(args.date or today_et(), backtest=args.backtest)
