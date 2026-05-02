from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from first_inning_lab.storage.json_store import atomic_write_json


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_historical_games(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")
    df = pd.read_csv(input_path)
    if df.empty:
        return df
    if "game_pk" not in df.columns and "game_id" in df.columns:
        df = df.rename(columns={"game_id": "game_pk"})
    if "game_pk" not in df.columns:
        df["game_pk"] = None
    df["game_date"] = pd.to_datetime(df.get("game_date"), errors="coerce")
    if "season" not in df.columns:
        df["season"] = df["game_date"].dt.year
    else:
        df["season"] = df["season"].fillna(df["game_date"].dt.year)
    return df


def _dedupe_games(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if df["game_pk"].notna().any():
        return df.drop_duplicates(subset=["game_pk"], keep="first")
    return df.drop_duplicates(subset=["game_date", "away_team_id", "home_team_id", "venue_id"], keep="first")


def build_half_inning_rows(games_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    rows: list[dict[str, Any]] = []
    skipped = 0
    for idx, row in games_df.iterrows():
        away_runs = row.get("away_runs_1st")
        home_runs = row.get("home_runs_1st")
        if pd.isna(away_runs) or pd.isna(home_runs):
            skipped += 1
            continue
        total_runs = row.get("total_runs_1st")
        if pd.isna(total_runs):
            total_runs = int(away_runs) + int(home_runs)
        base = {
            "game_pk": row.get("game_pk"),
            "game_date": row.get("game_date"),
            "season": row.get("season"),
            "venue_id": row.get("venue_id"),
            "total_runs_1st": total_runs,
            "game_nrfi_result": row.get("nrfi_result") if "nrfi_result" in row else int(total_runs == 0),
            "source_game_row_index": int(idx),
        }
        rows.append({**base, "inning_half": "top", "batting_team_id": row.get("away_team_id"), "batting_team_name": row.get("away_team"), "pitching_team_id": row.get("home_team_id"), "pitching_team_name": row.get("home_team"), "pitcher_id": row.get("home_starting_pitcher_id"), "is_home_batting_team": 0, "runs_scored_in_half": int(away_runs), "scored_binary": int(int(away_runs) > 0)})
        rows.append({**base, "inning_half": "bottom", "batting_team_id": row.get("home_team_id"), "batting_team_name": row.get("home_team"), "pitching_team_id": row.get("away_team_id"), "pitching_team_name": row.get("away_team"), "pitcher_id": row.get("away_starting_pitcher_id"), "is_home_batting_team": 1, "runs_scored_in_half": int(home_runs), "scored_binary": int(int(home_runs) > 0)})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["game_date"] = pd.to_datetime(out["game_date"], errors="coerce")
        out = out.sort_values(["game_date", "game_pk", "inning_half"]).reset_index(drop=True)
    return out, skipped


def compute_prior_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    all_dates = sorted(d for d in out["game_date"].dropna().unique())
    for i, d in enumerate(all_dates):
        prior = out[out["game_date"] < d]
        current_idx = out.index[out["game_date"] == d]
        league_n = len(prior)
        league_rate = prior["scored_binary"].mean() if league_n else None
        for idx in current_idx:
            r = out.loc[idx]
            team_prior = prior[prior["batting_team_id"] == r["batting_team_id"]] if pd.notna(r["batting_team_id"]) else prior.iloc[0:0]
            pitcher_prior = prior[prior["pitcher_id"] == r["pitcher_id"]] if pd.notna(r["pitcher_id"]) else prior.iloc[0:0]
            venue_prior = prior[prior["venue_id"] == r["venue_id"]] if pd.notna(r["venue_id"]) else prior.iloc[0:0]
            home_prior = team_prior[team_prior["is_home_batting_team"] == 1]
            away_prior = team_prior[team_prior["is_home_batting_team"] == 0]
            out.at[idx, "league_prior_half_inning_sample_size"] = league_n
            out.at[idx, "league_prior_half_inning_score_rate"] = league_rate
            out.at[idx, "batting_team_prior_sample_size"] = len(team_prior)
            out.at[idx, "batting_team_prior_first_inning_score_rate"] = team_prior["scored_binary"].mean() if len(team_prior) else None
            out.at[idx, "batting_team_prior_first_inning_runs_per_half"] = team_prior["runs_scored_in_half"].mean() if len(team_prior) else None
            out.at[idx, "pitcher_prior_sample_size"] = len(pitcher_prior)
            out.at[idx, "pitcher_prior_first_inning_score_allowed_rate"] = pitcher_prior["scored_binary"].mean() if len(pitcher_prior) else None
            out.at[idx, "pitcher_prior_first_inning_runs_allowed_per_half"] = pitcher_prior["runs_scored_in_half"].mean() if len(pitcher_prior) else None
            out.at[idx, "venue_prior_sample_size"] = len(venue_prior)
            out.at[idx, "venue_prior_first_inning_score_rate"] = venue_prior["scored_binary"].mean() if len(venue_prior) else None
            out.at[idx, "venue_prior_first_inning_runs_per_half"] = venue_prior["runs_scored_in_half"].mean() if len(venue_prior) else None
            out.at[idx, "batting_team_home_prior_score_rate"] = home_prior["scored_binary"].mean() if len(home_prior) else None
            out.at[idx, "batting_team_away_prior_score_rate"] = away_prior["scored_binary"].mean() if len(away_prior) else None
            if league_rate is None:
                out.at[idx, "batting_team_score_rate_smoothed"] = None
                out.at[idx, "pitcher_score_allowed_rate_smoothed"] = None
                out.at[idx, "venue_score_rate_smoothed"] = None
            else:
                out.at[idx, "batting_team_score_rate_smoothed"] = (team_prior["scored_binary"].sum() + league_rate * 20) / (len(team_prior) + 20)
                out.at[idx, "pitcher_score_allowed_rate_smoothed"] = (pitcher_prior["scored_binary"].sum() + league_rate * 10) / (len(pitcher_prior) + 10)
                out.at[idx, "venue_score_rate_smoothed"] = (venue_prior["scored_binary"].sum() + league_rate * 50) / (len(venue_prior) + 50)
    out["has_batting_team_history"] = out["batting_team_prior_sample_size"].fillna(0).astype(int) >= 20
    out["has_pitcher_history"] = out["pitcher_prior_sample_size"].fillna(0).astype(int) >= 5
    out["has_venue_history"] = out["venue_prior_sample_size"].fillna(0).astype(int) >= 20
    out["has_league_history"] = out["league_prior_half_inning_sample_size"].fillna(0).astype(int) >= 100
    out["half_inning_data_quality_score"] = (
        out["has_batting_team_history"].astype(float) * 0.30
        + out["has_pitcher_history"].astype(float) * 0.30
        + out["has_venue_history"].astype(float) * 0.20
        + out["has_league_history"].astype(float) * 0.20
    ).round(4)
    return out


def run(input_path: Path, output_csv: Path, output_json: Path, metadata_path: Path, start: str | None = None, end: str | None = None) -> dict:
    games = load_historical_games(input_path)
    games_read = len(games)
    if not games.empty:
        games = _dedupe_games(games)
        if start:
            games = games[games["game_date"] >= pd.to_datetime(start)]
        if end:
            games = games[games["game_date"] <= pd.to_datetime(end)]
    half_df, skipped = build_half_inning_rows(games)
    half_df = compute_prior_features(half_df)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    half_df_out = half_df.copy()
    if not half_df_out.empty:
        half_df_out["game_date"] = half_df_out["game_date"].dt.strftime("%Y-%m-%d")
    half_df_out.to_csv(output_csv, index=False)
    atomic_write_json(output_json, half_df_out.to_dict(orient="records"))
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "output_csv": str(output_csv),
        "output_json": str(output_json),
        "games_read": int(games_read),
        "games_skipped_missing_runs": int(skipped),
        "half_inning_rows_written": int(len(half_df_out)),
        "date_min": None if half_df.empty else half_df["game_date"].min().strftime("%Y-%m-%d"),
        "date_max": None if half_df.empty else half_df["game_date"].max().strftime("%Y-%m-%d"),
        "seasons": [] if half_df.empty else sorted([int(s) for s in pd.Series(half_df["season"]).dropna().unique().tolist()]),
        "rows_with_pitcher_id": int(half_df["pitcher_id"].notna().sum()) if "pitcher_id" in half_df else 0,
        "rows_with_venue_id": int(half_df["venue_id"].notna().sum()) if "venue_id" in half_df else 0,
        "rows_with_batting_team_history": int(half_df.get("has_batting_team_history", pd.Series(dtype=bool)).sum()),
        "rows_with_pitcher_history": int(half_df.get("has_pitcher_history", pd.Series(dtype=bool)).sum()),
        "rows_with_venue_history": int(half_df.get("has_venue_history", pd.Series(dtype=bool)).sum()),
        "rows_with_league_history": int(half_df.get("has_league_history", pd.Series(dtype=bool)).sum()),
        "no_leakage_rule": "rolling features use only games with game_date before current game_date",
    }
    atomic_write_json(metadata_path, metadata)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/historical/first_inning_results.csv")
    parser.add_argument("--output-csv", default="data/historical/half_inning_training_dataset.csv")
    parser.add_argument("--output-json", default="data/historical/half_inning_training_dataset.json")
    parser.add_argument("--metadata", default="data/historical/half_inning_training_metadata.json")
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()
    root = _root()
    md = run(root / args.input, root / args.output_csv, root / args.output_json, root / args.metadata, args.start, args.end)
    print(f"Half-inning training rows written: {md['half_inning_rows_written']}")


if __name__ == "__main__":
    main()
