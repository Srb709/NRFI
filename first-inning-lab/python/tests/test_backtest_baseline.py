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
