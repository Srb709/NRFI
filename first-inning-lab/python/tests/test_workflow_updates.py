import csv
from datetime import date

from first_inning_lab.features import historical_first_inning_features as hff
from first_inning_lab.pipelines import build_today_board, update_historical_first_innings


def test_update_history_dedupes_by_game_pk(monkeypatch, tmp_path):
    out = tmp_path / "data/historical"
    out.mkdir(parents=True)
    csv_path = out / "first_inning_results.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["game_pk", "game_date", "season"])
        w.writeheader(); w.writerow({"game_pk": "1", "game_date": "2025-04-01", "season": "2025"})

    def fake_build(start, end, outdir, verbose=True):
        with (outdir / "first_inning_results.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["game_pk", "game_date", "season"])
            w.writeheader(); w.writerow({"game_pk": "1", "game_date": "2025-04-01", "season": "2025"}); w.writerow({"game_pk": "2", "game_date": "2026-04-01", "season": "2026"})
        return {}

    monkeypatch.setattr(update_historical_first_innings, "_root", lambda: tmp_path)
    monkeypatch.setattr(update_historical_first_innings, "build_historical", fake_build)
    update_historical_first_innings.run("2026-04-01")
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 2


def test_today_board_uses_previous_day_season(monkeypatch):
    captured = {}
    monkeypatch.setattr(build_today_board, "get_schedule", lambda _d: [{"game_id": "1", "venue_id": 1, "start_time": "2026-05-02T20:00:00Z"}])
    monkeypatch.setattr(build_today_board, "read_json", lambda *a, **k: [{"venue_id": 1, "latitude": 0, "longitude": 0}])
    monkeypatch.setattr(build_today_board, "get_game_weather", lambda *a, **k: {"available": True})
    monkeypatch.setattr(build_today_board, "predict_baseline", lambda a: {"probability_available": False, "pricing_readiness": "unpriced", "feature_status": a["feature_status"], "data_quality_score": 0.0})
    monkeypatch.setattr(build_today_board, "atomic_write_json", lambda *a, **k: None)

    def fake_assemble(game, season, parks, weather):
        captured["season"] = season
        return {"feature_status": {"lineups_confirmed": False, "probable_pitchers_available": False, "pitcher_stats_available": False, "team_offense_stats_available": False, "park_factor_available": False, "historical_venue_factor_available": False, "park_or_venue_signal_available": False, "weather_available": False, "historical_first_inning_available": False}, "raw_features": {"historical_league": {}}, "warnings": []}

    monkeypatch.setattr(build_today_board, "assemble_game_features", fake_assemble)
    build_today_board.run("2026-05-02")
    assert captured["season"] == 2026


def test_unpriced_reasons_are_explicit():
    from first_inning_lab.modeling.baseline_rules_model import predict_baseline
    out = predict_baseline({"feature_status": {"probable_pitchers_available": False, "pitcher_stats_available": False, "team_offense_stats_available": False, "park_or_venue_signal_available": False, "historical_venue_factor_available": False, "weather_available": False, "lineups_confirmed": False}, "real_features": {}, "missing_data": [], "warnings": [], "data_quality_score": 0.0})
    assert "missing pitcher" in out["reasons"]
    assert "missing weather" in out["reasons"]
