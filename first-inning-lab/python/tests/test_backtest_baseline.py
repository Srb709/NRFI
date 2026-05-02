import csv
import json

from first_inning_lab.pipelines import backtest_baseline as bt


def _write_hist(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "game_pk","game_date","season","away_team","home_team","away_team_id","home_team_id","venue_id","venue_name",
        "away_starting_pitcher_id","home_starting_pitcher_id","away_starting_pitcher_name","home_starting_pitcher_name",
        "away_runs_1st","home_runs_1st","total_runs_1st",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _sample_rows():
    return [
        {"game_pk": 1, "game_date": "2025-03-27", "season": 2025, "away_team": "A", "home_team": "B", "away_team_id": 10, "home_team_id": 20, "venue_id": 1, "venue_name": "V1", "away_starting_pitcher_id": 100, "home_starting_pitcher_id": 200, "away_starting_pitcher_name": "PA", "home_starting_pitcher_name": "PB", "away_runs_1st": 0, "home_runs_1st": 0, "total_runs_1st": 0},
        {"game_pk": 2, "game_date": "2025-03-28", "season": 2025, "away_team": "A", "home_team": "C", "away_team_id": 10, "home_team_id": 30, "venue_id": 1, "venue_name": "V1", "away_starting_pitcher_id": 100, "home_starting_pitcher_id": 300, "away_starting_pitcher_name": "PA", "home_starting_pitcher_name": "PC", "away_runs_1st": 1, "home_runs_1st": 0, "total_runs_1st": 1},
        {"game_pk": 3, "game_date": "2025-03-29", "season": 2025, "away_team": "D", "home_team": "B", "away_team_id": 40, "home_team_id": 20, "venue_id": 2, "venue_name": "V2", "away_starting_pitcher_id": 400, "home_starting_pitcher_id": 200, "away_starting_pitcher_name": "PD", "home_starting_pitcher_name": "PB", "away_runs_1st": 0, "home_runs_1st": 1, "total_runs_1st": 1},
    ]


def test_no_same_game_data_leak():
    rows = _sample_rows()
    loaded = []
    for r in rows:
        loaded.append(bt.HistoricalGame(game_pk=r['game_pk'], game_date=bt._parse_date(r['game_date']), season=r['season'], away_team=r['away_team'], home_team=r['home_team'], away_team_id=r['away_team_id'], home_team_id=r['home_team_id'], venue_id=r['venue_id'], venue_name=r['venue_name'], away_starting_pitcher_id=r['away_starting_pitcher_id'], home_starting_pitcher_id=r['home_starting_pitcher_id'], away_starting_pitcher_name=r['away_starting_pitcher_name'], home_starting_pitcher_name=r['home_starting_pitcher_name'], away_runs_1st=r['away_runs_1st'], home_runs_1st=r['home_runs_1st'], total_runs_1st=r['total_runs_1st']))
    features = bt._build_features(loaded[0], [])
    assert features["real_features"]["pitcher_safety_score"] is None


def test_pass_not_counted_as_win_loss(monkeypatch, tmp_path):
    _write_hist(tmp_path / "data/historical/first_inning_results.csv", _sample_rows())
    monkeypatch.setattr(bt, "_root", lambda: tmp_path)
    out = bt.run("2025-03-27", "2025-03-29")
    assert out["summary"]["priced_games"] + out["summary"]["passes"] == out["summary"]["total_games_tested"]
    assert out["summary"]["wins"] + out["summary"]["losses"] == out["summary"]["priced_games"]


def test_grading_logic():
    assert bt._grade_prediction("PASS", 0) == ("NRFI", "PASS")
    assert bt._grade_prediction("NRFI", 0) == ("NRFI", "W")
    assert bt._grade_prediction("NRFI", 1) == ("YRFI", "L")
    assert bt._grade_prediction("YRFI", 2) == ("YRFI", "W")


def test_summary_math_and_output_files(monkeypatch, tmp_path):
    _write_hist(tmp_path / "data/historical/first_inning_results.csv", _sample_rows())
    monkeypatch.setattr(bt, "_root", lambda: tmp_path)
    out = bt.run("2025-03-27", "2025-03-29")
    summary = out["summary"]
    assert summary["total_games_tested"] == 3
    assert (tmp_path / "data/history/backtest_results.csv").exists()
    assert (tmp_path / "data/history/backtest_results.json").exists()
    assert (tmp_path / "data/history/backtest_summary.json").exists()
    payload = json.loads((tmp_path / "data/history/backtest_summary.json").read_text())
    assert payload["total_games_tested"] == 3


def test_bucket_details_and_calibration_math():
    results = [
        {"outcome": "W", "lean": "NRFI", "actual": "NRFI", "nrfi_probability": 0.66, "yrfi_probability": 0.34, "confidence_tier": "A", "probability_bucket": "65+", "board_type": "final_board", "data_quality_score": 0.8},
        {"outcome": "L", "lean": "NRFI", "actual": "YRFI", "nrfi_probability": 0.67, "yrfi_probability": 0.33, "confidence_tier": "A", "probability_bucket": "65+", "board_type": "final_board", "data_quality_score": 0.6},
        {"outcome": "PASS", "lean": "PASS", "actual": "NRFI", "nrfi_probability": 0.52, "yrfi_probability": 0.48, "confidence_tier": "PASS", "probability_bucket": "50-54", "board_type": "early_board", "data_quality_score": 0.2},
    ]
    summary = bt._compute_summary(results)
    assert summary["probability_bucket_details"]["65+"]["count"] == 2
    assert summary["probability_bucket_details"]["50-54"]["count"] == 0
    assert summary["probability_bucket_details"]["65+"]["actual_nrfi_rate"] == 0.5
    assert summary["probability_bucket_details"]["65+"]["calibration_error"] == -0.165
    assert summary["nrfi_pick_summary"]["count"] == 2


def test_overall_mae_uses_buckets_with_min_count():
    results = []
    for _ in range(30):
        results.append({"outcome": "W", "lean": "NRFI", "actual": "NRFI", "nrfi_probability": 0.6, "yrfi_probability": 0.4, "confidence_tier": "A", "probability_bucket": "60-64", "board_type": "final_board", "data_quality_score": 0.9})
    for _ in range(10):
        results.append({"outcome": "L", "lean": "NRFI", "actual": "YRFI", "nrfi_probability": 0.66, "yrfi_probability": 0.34, "confidence_tier": "A", "probability_bucket": "65+", "board_type": "final_board", "data_quality_score": 0.9})
    summary = bt._compute_summary(results)
    assert summary["overall_mean_absolute_calibration_error_for_buckets_count_ge_30"] == 0.4
