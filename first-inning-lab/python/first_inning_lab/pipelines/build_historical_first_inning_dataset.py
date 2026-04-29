from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from first_inning_lab.data_sources.mlb_stats_api import get_game_feed, get_linescore, get_schedule

SKIP_STATUSES = {"Postponed", "Cancelled", "Suspended"}


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _build_row(g: dict, ls: dict, feed: dict) -> dict | None:
    innings = ls.get("innings") or []
    if not innings:
        return None
    first = innings[0] if innings else None
    if not first:
        return None
    away_runs = (first.get("away") or {}).get("runs")
    home_runs = (first.get("home") or {}).get("runs")
    if away_runs is None or home_runs is None:
        return None
    probable = ((feed.get("gameData") or {}).get("probablePitchers") or {}) if isinstance(feed, dict) else {}
    total = int(away_runs) + int(home_runs)
    return {
        "game_pk": g.get("game_pk"), "game_date": g.get("game_date"), "season": int((g.get("game_date") or "0000")[:4]),
        "away_team": g.get("away_team"), "home_team": g.get("home_team"), "away_team_id": g.get("away_team_id"), "home_team_id": g.get("home_team_id"),
        "venue_id": g.get("venue_id"), "venue_name": g.get("venue"), "game_status": g.get("status"),
        "away_starting_pitcher_name": (probable.get("away") or {}).get("fullName") or g.get("away_probable_pitcher"),
        "home_starting_pitcher_name": (probable.get("home") or {}).get("fullName") or g.get("home_probable_pitcher"),
        "away_starting_pitcher_id": (probable.get("away") or {}).get("id") or g.get("away_probable_pitcher_id"),
        "home_starting_pitcher_id": (probable.get("home") or {}).get("id") or g.get("home_probable_pitcher_id"),
        "away_runs_1st": int(away_runs), "home_runs_1st": int(home_runs), "total_runs_1st": total,
        "nrfi_result": total == 0, "yrfi_result": total > 0,
        "final_away_runs": (ls.get("teams") or {}).get("away", {}).get("runs"), "final_home_runs": (ls.get("teams") or {}).get("home", {}).get("runs"),
    }


def run(start: str, end: str, outdir: Path | None = None) -> dict:
    s = datetime.fromisoformat(start).date(); e = datetime.fromisoformat(end).date()
    outdir = outdir or (_root() / "data/historical")
    outdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    warnings: list[str] = []
    games_found = games_skipped = dates_processed = 0
    for d in _daterange(s, e):
        dates_processed += 1
        try:
            games = get_schedule(d.isoformat()) or []
        except Exception as exc:
            warnings.append(f"{d.isoformat()}: schedule fetch failed ({exc}).")
            continue
        for g in games:
            games_found += 1
            status = g.get("status")
            if status in SKIP_STATUSES:
                games_skipped += 1
                continue
            try:
                ls = get_linescore(g.get("game_pk")) or {}
            except Exception as exc:
                warnings.append(f"{g.get('game_pk')}: linescore fetch failed ({exc}).")
                games_skipped += 1
                continue
            if not ls:
                warnings.append(f"{g.get('game_pk')}: linescore missing.")
                games_skipped += 1
                continue
            try:
                feed = get_game_feed(g.get("game_pk")) or {}
            except Exception:
                feed = {}
            row = _build_row(g, ls, feed)
            if not row:
                warnings.append(f"{g.get('game_pk')}: first inning unavailable.")
                games_skipped += 1
                continue
            rows.append(row)
    rows.sort(key=lambda x: (x.get("game_date"), x.get("game_pk")))
    csv_path = outdir / "first_inning_results.csv"
    json_path = outdir / "first_inning_results.json"
    meta_path = outdir / "historical_build_metadata.json"
    fields = list(rows[0].keys()) if rows else ["game_pk","game_date","season","away_team","home_team","away_team_id","home_team_id","venue_id","venue_name","game_status","away_starting_pitcher_name","home_starting_pitcher_name","away_starting_pitcher_id","home_starting_pitcher_id","away_runs_1st","home_runs_1st","total_runs_1st","nrfi_result","yrfi_result","final_away_runs","final_home_runs"]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    metadata = {"generated_at": datetime.utcnow().isoformat() + "Z", "start": start, "end": end, "dates_processed": dates_processed, "games_found": games_found, "games_written": len(rows), "games_skipped": games_skipped, "warnings_count": len(warnings), "warnings": warnings}
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    args = ap.parse_args()
    run(args.start, args.end)
