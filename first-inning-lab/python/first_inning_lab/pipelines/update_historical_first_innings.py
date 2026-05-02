from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from first_inning_lab.pipelines.build_historical_first_inning_dataset import run as build_historical


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_through_date() -> str:
    return (datetime.now(ZoneInfo("America/New_York")).date() - timedelta(days=1)).isoformat()


def run(through: str | None = None) -> dict:
    through = through or _default_through_date()
    outdir = _root() / "data/historical"
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "first_inning_results.csv"

    existing_rows = []
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as fh:
            existing_rows = list(csv.DictReader(fh))

    earliest = min((r.get("game_date") for r in existing_rows if r.get("game_date")), default=through)
    build_historical(earliest, through, outdir=outdir, verbose=True)

    with csv_path.open(newline="", encoding="utf-8") as fh:
        all_rows = list(csv.DictReader(fh))

    by_game_pk = {}
    for row in all_rows:
        by_game_pk[str(row.get("game_pk"))] = row
    merged = list(by_game_pk.values())
    merged.sort(key=lambda x: (x.get("game_date"), int(x.get("game_pk") or 0)))

    fields = list(merged[0].keys()) if merged else []
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(merged)

    (outdir / "first_inning_results.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "append_update",
        "through": through,
        "existing_games": len(existing_rows),
        "total_games": len(merged),
        "new_games_added": max(0, len(merged) - len(existing_rows)),
    }
    (outdir / "historical_update_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--through")
    args = parser.parse_args()
    run(args.through)
