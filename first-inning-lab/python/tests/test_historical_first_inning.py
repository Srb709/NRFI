import csv
import json
from pathlib import Path

from first_inning_lab.features import historical_first_inning_features as hff
from first_inning_lab.modeling.baseline_rules_model import predict_baseline
from first_inning_lab.pipelines import build_historical_first_inning_dataset as builder


def test_builder_nrfi_and_yrfi(monkeypatch, tmp_path):
    monkeypatch.setattr(builder, "_root", lambda: tmp_path)
    monkeypatch.setattr(builder, "get_schedule", lambda _d: [
        {"game_pk": 1, "game_date": "2025-03-27", "away_team": "A", "home_team": "B", "away_team_id": 10, "home_team_id": 11, "venue_id": 1, "venue": "V", "status": "Final"},
        {"game_pk": 2, "game_date": "2025-03-27", "away_team": "C", "home_team": "D", "away_team_id": 12, "home_team_id": 13, "venue_id": 1, "venue": "V", "status": "Final"},
        {"game_pk": 3, "game_date": "2025-03-27", "away_team": "E", "home_team": "F", "away_team_id": 14, "home_team_id": 15, "venue_id": 1, "venue": "V", "status": "Postponed"},
    ])
    monkeypatch.setattr(builder, "get_game_feed", lambda _g: {"gameData": {"probablePitchers": {}}})
    monkeypatch.setattr(builder, "get_linescore", lambda g: {"innings": [{"away": {"runs": 0 if g == 1 else 1}, "home": {"runs": 0}}], "teams": {"away": {"runs": 2}, "home": {"runs": 1}}})
    meta = builder.run("2025-03-27", "2025-03-27")
    rows = list(csv.DictReader((tmp_path / "data/historical/first_inning_results.csv").open()))
    assert len(rows) == 2
    assert rows[0]["nrfi_result"] == "True"
    assert rows[1]["yrfi_result"] == "True"
    assert meta["games_skipped"] == 1


def test_missing_linescore_warns(monkeypatch, tmp_path):
    monkeypatch.setattr(builder, "_root", lambda: tmp_path)
    monkeypatch.setattr(builder, "get_schedule", lambda _d: [{"game_pk": 1, "game_date": "2025-03-27", "status": "Final"}])
    monkeypatch.setattr(builder, "get_linescore", lambda _g: {})
    monkeypatch.setattr(builder, "get_game_feed", lambda _g: {})
    meta = builder.run("2025-03-27", "2025-03-27")
    assert meta["warnings_count"] == 1


def test_historical_features_thresholds(tmp_path, monkeypatch):
    p = tmp_path / "first_inning_results.csv"
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["season","venue_id","total_runs_1st","nrfi_result","away_team_id","home_team_id","away_runs_1st","home_runs_1st","away_starting_pitcher_id","home_starting_pitcher_id"])
        w.writeheader()
        for i in range(120):
            w.writerow({"season": 2025, "venue_id": 1 if i < 25 else 2, "total_runs_1st": 1 if i < 25 else 0, "nrfi_result": False if i < 25 else True, "away_team_id": 10, "home_team_id": 11, "away_runs_1st": 1, "home_runs_1st": 0, "away_starting_pitcher_id": 50, "home_starting_pitcher_id": 51})
    monkeypatch.setattr(hff, "_dataset_path", lambda: p)
    lg = hff.get_league_first_inning_baseline(2025)
    v = hff.get_venue_first_inning_factor(1, 2025)
    assert lg["available"] is True
    assert v["available"] is True
    assert round(v["venue_first_inning_run_factor"], 3) == round(v["venue_avg_first_inning_runs"] / lg["league_avg_first_inning_runs"], 3)
    assert hff.get_pitcher_first_inning_profile(999, 2025)["available"] is False


def test_model_uses_historical_venue_for_pricing():
    out = predict_baseline({"feature_status": {"probable_pitchers_available": True, "pitcher_stats_available": True, "team_offense_stats_available": True, "park_or_venue_signal_available": True, "lineups_confirmed": False}, "real_features": {"pitcher_safety_score": 0.6, "offense_danger_score": 0.4, "park_weather_score": None, "venue_first_inning_score": 0.55}, "missing_data": [], "warnings": [], "data_quality_score": 0.8})
    assert out["probability_available"] is True
    assert out["pricing_readiness"] == "priced_core_early"


def test_model_blocks_without_park_or_venue():
    out = predict_baseline({"feature_status": {"probable_pitchers_available": True, "pitcher_stats_available": True, "team_offense_stats_available": True, "park_or_venue_signal_available": False, "lineups_confirmed": False}, "real_features": {"pitcher_safety_score": 0.6, "offense_danger_score": 0.4, "park_weather_score": None, "venue_first_inning_score": None}, "missing_data": [], "warnings": [], "data_quality_score": 0.8})
    assert out["pricing_readiness"] == "unpriced_missing_core_inputs"

def _write_hist_csv(path, rows):
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["season","venue_id","total_runs_1st","nrfi_result","away_team_id","home_team_id","away_runs_1st","home_runs_1st","away_starting_pitcher_id","home_starting_pitcher_id"])
        w.writeheader()
        for row in rows:
            w.writerow(row)


def test_historical_season_fallback_to_prior(monkeypatch, tmp_path):
    p = tmp_path / "first_inning_results.csv"
    rows = [{"season": 2025, "venue_id": 1, "total_runs_1st": 1, "nrfi_result": False, "away_team_id": 10, "home_team_id": 11, "away_runs_1st": 1, "home_runs_1st": 0, "away_starting_pitcher_id": 50, "home_starting_pitcher_id": 51} for _ in range(120)]
    _write_hist_csv(p, rows)
    monkeypatch.setattr(hff, "_dataset_path", lambda: p)

    lg = hff.get_league_first_inning_baseline(2026)
    v = hff.get_venue_first_inning_factor(1, 2026)
    assert lg["available"] is True
    assert lg["requested_season"] == 2026
    assert lg["used_season"] == 2025
    assert lg["season_fallback_used"] is True
    assert any("Using prior historical season 2025 for 2026 board." in x for x in lg["warnings"])
    assert v["used_season"] == 2025
    assert v["season_fallback_used"] is True


def test_historical_season_no_fallback_when_requested_has_data(monkeypatch, tmp_path):
    p = tmp_path / "first_inning_results.csv"
    rows = [{"season": 2026, "venue_id": 1, "total_runs_1st": 1, "nrfi_result": False, "away_team_id": 10, "home_team_id": 11, "away_runs_1st": 1, "home_runs_1st": 0, "away_starting_pitcher_id": 50, "home_starting_pitcher_id": 51} for _ in range(120)]
    _write_hist_csv(p, rows)
    monkeypatch.setattr(hff, "_dataset_path", lambda: p)

    lg = hff.get_league_first_inning_baseline(2026)
    assert lg["available"] is True
    assert lg["used_season"] == 2026
    assert lg["season_fallback_used"] is False


def test_historical_season_unavailable_without_prior(monkeypatch, tmp_path):
    p = tmp_path / "first_inning_results.csv"
    rows = [{"season": 2026, "venue_id": 1, "total_runs_1st": 0, "nrfi_result": True, "away_team_id": 10, "home_team_id": 11, "away_runs_1st": 0, "home_runs_1st": 0, "away_starting_pitcher_id": 50, "home_starting_pitcher_id": 51} for _ in range(10)]
    _write_hist_csv(p, rows)
    monkeypatch.setattr(hff, "_dataset_path", lambda: p)

    lg = hff.get_league_first_inning_baseline(2027)
    assert lg["available"] is False
    assert lg["requested_season"] == 2027
    assert lg["used_season"] == 2027
    assert lg["season_fallback_used"] is False
    assert any("below threshold" in x.lower() for x in lg["warnings"])


def test_build_today_board_message_when_dataset_exists_below_threshold(monkeypatch, capsys):
    from first_inning_lab.pipelines import build_today_board as btb

    game = {"game_id": "1", "venue_id": 1, "start_time": "2026-04-29T23:00:00Z", "away_team": "A", "home_team": "B"}
    monkeypatch.setattr(btb, "get_schedule", lambda _d: [game])
    monkeypatch.setattr(btb, "read_json", lambda *a, **k: [{"venue_id": 1, "latitude": 1.0, "longitude": 1.0}])
    monkeypatch.setattr(btb, "get_game_weather", lambda *a, **k: {"available": False})
    monkeypatch.setattr(btb, "atomic_write_json", lambda *a, **k: None)
    monkeypatch.setattr(
        btb,
        "assemble_game_features",
        lambda *a, **k: {
            "feature_status": {
                "lineups_confirmed": False,
                "probable_pitchers_available": True,
                "pitcher_stats_available": True,
                "team_offense_stats_available": True,
                "park_factor_available": False,
                "historical_venue_factor_available": False,
                "park_or_venue_signal_available": False,
                "weather_available": False,
                "historical_first_inning_available": False,
            },
            "raw_features": {"historical_league": {"available": False, "warnings": ["Historical first-inning sample below threshold."]}},
            "warnings": [],
        },
    )
    monkeypatch.setattr(btb, "predict_baseline", lambda assembled: {"probability_available": False, "pricing_readiness": "unpriced", "feature_status": assembled["feature_status"], "data_quality_score": 0.0})

    btb.run("2026-04-29")
    out = capsys.readouterr().out
    assert "run build_historical_first_inning_dataset" not in out
    assert "Historical dataset below threshold: 1" in out


def test_entity_season_fallback_uses_prior_when_requested_season_entity_sample_is_low(monkeypatch, tmp_path):
    p = tmp_path / "first_inning_results.csv"
    rows = []
    rows.extend([
        {"season": 2025, "venue_id": 1, "total_runs_1st": 1, "nrfi_result": False, "away_team_id": 10, "home_team_id": 11, "away_runs_1st": 1, "home_runs_1st": 0, "away_starting_pitcher_id": 50, "home_starting_pitcher_id": 999}
        for _ in range(25)
    ])
    rows.extend([
        {"season": 2025, "venue_id": 2, "total_runs_1st": 0, "nrfi_result": True, "away_team_id": 20, "home_team_id": 21, "away_runs_1st": 0, "home_runs_1st": 0, "away_starting_pitcher_id": 60, "home_starting_pitcher_id": 61}
        for _ in range(95)
    ])
    for i in range(5):
        rows.append(
            {
                "season": 2026,
                "venue_id": 1,
                "total_runs_1st": 1,
                "nrfi_result": False,
                "away_team_id": 10,
                "home_team_id": 11,
                "away_runs_1st": 1,
                "home_runs_1st": 0,
                "away_starting_pitcher_id": 50 if i < 4 else 52,
                "home_starting_pitcher_id": 999,
            }
        )
    rows.extend([
        {"season": 2026, "venue_id": 2, "total_runs_1st": 0, "nrfi_result": True, "away_team_id": 20, "home_team_id": 21, "away_runs_1st": 0, "home_runs_1st": 0, "away_starting_pitcher_id": 60, "home_starting_pitcher_id": 61}
        for _ in range(115)
    ])
    _write_hist_csv(p, rows)
    monkeypatch.setattr(hff, "_dataset_path", lambda: p)

    venue = hff.get_venue_first_inning_factor(1, 2026)
    assert venue["available"] is True
    assert venue["used_season"] == 2025
    assert venue["season_fallback_used"] is True
    assert venue["sample_size"] == 25
    assert any("Using prior historical season 2025 for 2026 venue factor." in x for x in venue["warnings"])

    team = hff.get_team_first_inning_profile(10, 2026)
    assert team["available"] is True
    assert team["used_season"] == 2025
    assert team["season_fallback_used"] is True
    assert team["sample_size"] == 25
    assert any("Using prior historical season 2025 for 2026 team factor." in x for x in team["warnings"])

    pitcher = hff.get_pitcher_first_inning_profile(50, 2026)
    assert pitcher["available"] is True
    assert pitcher["used_season"] == 2025
    assert pitcher["season_fallback_used"] is True
    assert pitcher["sample_size"] == 25
    assert any("Using prior historical season 2025 for 2026 pitcher factor." in x for x in pitcher["warnings"])
