from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from first_inning_lab.modeling.baseline_rules_model import predict_baseline


@dataclass(frozen=True)
class HistoricalGame:
    game_pk: int
    game_date: date
    season: int
    away_team: str
    home_team: str
    away_team_id: int
    home_team_id: int
    venue_id: int
    venue_name: str
    away_starting_pitcher_id: int
    home_starting_pitcher_id: int
    away_starting_pitcher_name: str
    home_starting_pitcher_name: str
    away_runs_1st: int
    home_runs_1st: int
    total_runs_1st: int


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _parse_int(value: str | int | None, default: int = -1) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def _parse_date(value: str) -> date:
    return datetime.fromisoformat(value[:10]).date()


def _load_games(path: Path, start: date | None = None, end: date | None = None) -> list[HistoricalGame]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    games: list[HistoricalGame] = []
    for row in rows:
        gd = _parse_date(row["game_date"])
        if start and gd < start:
            continue
        if end and gd > end:
            continue
        games.append(
            HistoricalGame(
                game_pk=_parse_int(row.get("game_pk")),
                game_date=gd,
                season=_parse_int(row.get("season"), gd.year),
                away_team=row.get("away_team") or "",
                home_team=row.get("home_team") or "",
                away_team_id=_parse_int(row.get("away_team_id")),
                home_team_id=_parse_int(row.get("home_team_id")),
                venue_id=_parse_int(row.get("venue_id")),
                venue_name=row.get("venue_name") or row.get("venue") or "",
                away_starting_pitcher_id=_parse_int(row.get("away_starting_pitcher_id")),
                home_starting_pitcher_id=_parse_int(row.get("home_starting_pitcher_id")),
                away_starting_pitcher_name=row.get("away_starting_pitcher_name") or "",
                home_starting_pitcher_name=row.get("home_starting_pitcher_name") or "",
                away_runs_1st=_parse_int(row.get("away_runs_1st"), 0),
                home_runs_1st=_parse_int(row.get("home_runs_1st"), 0),
                total_runs_1st=_parse_int(row.get("total_runs_1st"), 0),
            )
        )
    return sorted(games, key=lambda g: (g.game_date, g.game_pk))


def _avg(values: list[float]) -> float | None:
    return (sum(values) / len(values)) if values else None


def _build_features(game: HistoricalGame, prior_games: list[HistoricalGame]) -> dict:
    team_games = [g for g in prior_games if game.away_team_id in (g.away_team_id, g.home_team_id) or game.home_team_id in (g.away_team_id, g.home_team_id)]
    away_pitcher_games = [g for g in prior_games if game.away_starting_pitcher_id in (g.away_starting_pitcher_id, g.home_starting_pitcher_id)]
    home_pitcher_games = [g for g in prior_games if game.home_starting_pitcher_id in (g.away_starting_pitcher_id, g.home_starting_pitcher_id)]
    venue_games = [g for g in prior_games if g.venue_id == game.venue_id]

    away_pitcher_allowed = [g.home_runs_1st if g.away_starting_pitcher_id == game.away_starting_pitcher_id else g.away_runs_1st for g in away_pitcher_games]
    home_pitcher_allowed = [g.home_runs_1st if g.away_starting_pitcher_id == game.home_starting_pitcher_id else g.away_runs_1st for g in home_pitcher_games]
    pitcher_allowed = away_pitcher_allowed + home_pitcher_allowed

    offense_scored = []
    for g in team_games:
        if g.away_team_id == game.away_team_id:
            offense_scored.append(g.away_runs_1st)
        elif g.home_team_id == game.away_team_id:
            offense_scored.append(g.home_runs_1st)
        if g.away_team_id == game.home_team_id:
            offense_scored.append(g.away_runs_1st)
        elif g.home_team_id == game.home_team_id:
            offense_scored.append(g.home_runs_1st)

    pitch_avg = _avg([float(x) for x in pitcher_allowed])
    offense_avg = _avg([float(x) for x in offense_scored])
    venue_avg = _avg([float(g.total_runs_1st) for g in venue_games])

    pitcher_safety = None if pitch_avg is None else max(0.0, min(1.0, 1.0 - (pitch_avg / 2.0)))
    offense_danger = None if offense_avg is None else max(0.0, min(1.0, offense_avg / 1.5))
    venue_score = None if venue_avg is None else max(0.0, min(1.0, venue_avg / 2.0))

    probable = game.away_starting_pitcher_id > 0 and game.home_starting_pitcher_id > 0
    pitcher_ok = pitch_avg is not None and len(away_pitcher_games) >= 1 and len(home_pitcher_games) >= 1
    offense_ok = offense_avg is not None and len(team_games) >= 2
    venue_ok = venue_score is not None and len(venue_games) >= 1

    feature_status = {
        "probable_pitchers_available": probable,
        "pitcher_stats_available": pitcher_ok,
        "team_offense_stats_available": offense_ok,
        "park_factor_available": False,
        "historical_venue_factor_available": venue_ok,
        "park_or_venue_signal_available": venue_ok,
        "weather_available": False,
        "lineups_confirmed": True,
    }

    avail_count = sum([probable, pitcher_ok, offense_ok, venue_ok, False, True])
    return {
        "feature_status": feature_status,
        "real_features": {
            "pitcher_safety_score": pitcher_safety,
            "offense_danger_score": offense_danger,
            "park_weather_score": None,
            "venue_first_inning_score": venue_score,
            "recent_form_score": None,
        },
        "missing_data": [],
        "warnings": [],
        "data_quality_score": round(avail_count / 6.0, 3),
    }


def _grade_prediction(lean: str, total_runs_1st: int) -> tuple[str, str]:
    actual = "NRFI" if total_runs_1st == 0 else "YRFI"
    if lean == "PASS":
        return actual, "PASS"
    return actual, ("W" if lean == actual else "L")


def _probability_bucket(pred: dict) -> str:
    p = pred.get("nrfi_probability")
    if p is None:
        return "unpriced"
    pct = round(float(p) * 100)
    for lo, hi in [(35, 39), (40, 44), (45, 49), (50, 54), (55, 59), (60, 64)]:
        if lo <= pct <= hi:
            return f"{lo}-{hi}"
    return "65+" if pct >= 65 else "below_35"


def _compute_summary(results: list[dict]) -> dict:
    priced = [r for r in results if r["outcome"] != "PASS"]
    wins = [r for r in priced if r["outcome"] == "W"]
    losses = [r for r in priced if r["outcome"] == "L"]
    nrfi = [r for r in priced if r["lean"] == "NRFI"]
    yrfi = [r for r in priced if r["lean"] == "YRFI"]

    def rate(rows: list[dict]) -> float | None:
        return round(sum(1 for r in rows if r["outcome"] == "W") / len(rows), 4) if rows else None

    by_conf = defaultdict(list)
    by_bucket = defaultdict(list)
    by_board = defaultdict(list)
    for row in priced:
        by_conf[row.get("confidence_tier")].append(row)
        by_bucket[row.get("probability_bucket")].append(row)
        by_board[row.get("board_type")].append(row)

    return {
        "total_games_tested": len(results),
        "priced_games": len(priced),
        "passes": sum(1 for r in results if r["outcome"] == "PASS"),
        "nrfi_picks": len(nrfi),
        "yrfi_picks": len(yrfi),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": rate(priced),
        "nrfi_win_rate": rate(nrfi),
        "yrfi_win_rate": rate(yrfi),
        "win_rate_by_confidence_tier": {k: rate(v) for k, v in sorted(by_conf.items())},
        "win_rate_by_probability_bucket": {k: rate(by_bucket.get(k, [])) for k in ["35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]},
        "win_rate_by_board_type": {k: rate(by_board.get(k, [])) for k in ["early_board", "final_board"]},
        "average_data_quality": round(sum(float(r["data_quality_score"]) for r in results) / len(results), 4) if results else None,
        "average_data_quality_wins": round(sum(float(r["data_quality_score"]) for r in wins) / len(wins), 4) if wins else None,
        "average_data_quality_losses": round(sum(float(r["data_quality_score"]) for r in losses) / len(losses), 4) if losses else None,
    }


def run(start: str | None = None, end: str | None = None) -> dict:
    root = _root()
    source = root / "data/historical/first_inning_results.csv"
    out_dir = root / "data/history"
    out_dir.mkdir(parents=True, exist_ok=True)

    start_d = _parse_date(start) if start else None
    end_d = _parse_date(end) if end else None
    games = _load_games(source, start_d, end_d)

    results = []
    prior_games: list[HistoricalGame] = []
    for game in games:
        assembled = _build_features(game, prior_games)
        pred = predict_baseline(assembled)
        actual, outcome = _grade_prediction(pred.get("lean", "PASS"), game.total_runs_1st)
        board_type = "final_board" if assembled["feature_status"].get("lineups_confirmed") else "early_board"

        row = {
            "game_pk": game.game_pk,
            "game_date": game.game_date.isoformat(),
            "season": game.season,
            "away_team": game.away_team,
            "home_team": game.home_team,
            "lean": pred.get("lean"),
            "actual": actual,
            "outcome": outcome,
            "nrfi_probability": pred.get("nrfi_probability"),
            "yrfi_probability": pred.get("yrfi_probability"),
            "confidence_tier": pred.get("confidence_tier"),
            "board_type": board_type,
            "data_quality_score": pred.get("data_quality_score", 0.0),
            "total_runs_1st": game.total_runs_1st,
        }
        row["probability_bucket"] = _probability_bucket(row)
        results.append(row)
        prior_games.append(game)

    summary = _compute_summary(results)
    csv_path = out_dir / "backtest_results.csv"
    json_path = out_dir / "backtest_results.json"
    summary_path = out_dir / "backtest_summary.json"

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0].keys()) if results else ["game_pk", "game_date"])
        writer.writeheader()
        writer.writerows(results)
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Baseline NRFI/YRFI Backtest")
    print(f"Window: {start or 'ALL'} to {end or 'ALL'}")
    print(f"Games tested: {summary['total_games_tested']}")
    print(f"Priced games: {summary['priced_games']} | Passes: {summary['passes']}")
    print(f"Wins: {summary['wins']} | Losses: {summary['losses']} | Win rate: {summary['win_rate']}")
    print(f"NRFI picks: {summary['nrfi_picks']} | YRFI picks: {summary['yrfi_picks']}")
    print(f"Average data quality: {summary['average_data_quality']}")

    return {"results": results, "summary": summary, "files": {"csv": str(csv_path), "json": str(json_path), "summary": str(summary_path)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()
    run(args.start, args.end)
