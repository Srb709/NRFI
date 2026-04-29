from first_inning_lab.data_sources import mlb_stats_api
from first_inning_lab.data_sources import player_stats_provider as psp
from first_inning_lab.data_sources import team_stats_provider as tsp
from first_inning_lab.features import assemble_game_features as agf
from first_inning_lab.modeling.baseline_rules_model import predict_baseline
from first_inning_lab.pipelines import build_today_board


def test_mlb_player_stats_helper_parses(monkeypatch):
    monkeypatch.setattr(mlb_stats_api, "safe_get_json", lambda _u: {"stats": [{"splits": [{"stat": {"gamesPlayed": "5", "inningsPitched": "20.1", "era": "3.20", "whip": "1.10", "strikeOuts": "30", "baseOnBalls": "10", "homeRuns": "2", "battersFaced": "80"}}]}]})
    out = mlb_stats_api.get_player_season_stats(1, 2026, "pitching")
    assert out["available"] and out["stats"]["gamesPlayed"] == 5


def test_mlb_player_stats_helper_unavailable(monkeypatch):
    monkeypatch.setattr(mlb_stats_api, "safe_get_json", lambda _u: {})
    out = mlb_stats_api.get_player_season_stats(1, 2026, "pitching")
    assert out["available"] is False


def test_player_provider_uses_person_id(monkeypatch):
    calls = []
    monkeypatch.setattr(psp, "read_json", lambda *a, **k: None)
    monkeypatch.setattr(psp, "atomic_write_json", lambda *a, **k: None)
    def fake(pid, season, group):
        calls.append(pid)
        return {"available": True, "stats": {"gamesPlayed": 2, "inningsPitched": 9, "era": 2.0, "whip": 1.0, "strikeOuts": 8, "baseOnBalls": 1, "homeRuns": 0, "battersFaced": 34, "numberOfPitches": 120}}
    monkeypatch.setattr(psp, "get_player_season_stats", fake)
    out = psp.get_pitcher_stats(656876, "name", 2026)
    assert out["available"] and calls[0] == 656876


def test_previous_season_fallback_pitcher(monkeypatch):
    monkeypatch.setattr(psp, "read_json", lambda *a, **k: None)
    monkeypatch.setattr(psp, "atomic_write_json", lambda *a, **k: None)
    monkeypatch.setattr(psp, "get_player_season_stats", lambda _id, season, _g: {"available": True, "stats": {"gamesPlayed": 0, "inningsPitched": 0}} if season == 2026 else {"available": True, "stats": {"gamesPlayed": 20, "inningsPitched": 100, "era": 3, "whip": 1.1, "strikeOuts": 100, "baseOnBalls": 20, "homeRuns": 10, "battersFaced": 400, "numberOfPitches": 1400}})
    out = psp.get_pitcher_stats(1, "name", 2026)
    assert out["source"].endswith("previous_season")


def test_team_provider_by_team_id(monkeypatch):
    monkeypatch.setattr(tsp, "read_json", lambda *a, **k: None)
    monkeypatch.setattr(tsp, "atomic_write_json", lambda *a, **k: None)
    monkeypatch.setattr(tsp, "get_team_season_stats", lambda tid, season, group: {"available": True, "stats": {"gamesPlayed": 10, "runs": 50, "plateAppearances": 380, "obp": 0.33, "slg": 0.42, "ops": 0.75, "strikeOuts": 80, "baseOnBalls": 30}})
    out = tsp.get_team_offense_stats(139, "Whatever Name", 2026)
    assert out["available"] and out["source"] == "mlb_stats_api_team_hitting"


def test_feature_assembler_availability(monkeypatch):
    monkeypatch.setattr(agf, "get_pitcher_stats", lambda *a, **k: {"available": True, "features": {"era": 3, "whip": 1.1}, "warnings": []})
    monkeypatch.setattr(agf, "get_team_offense_stats", lambda *a, **k: {"available": True, "features": {"ops": 0.75, "runs_per_game": 4.8}, "warnings": []})
    monkeypatch.setattr(agf, "get_lineup_data", lambda *_a, **_k: {"lineups_confirmed": True, "warnings": []})
    monkeypatch.setattr(agf, "build_park_weather_features", lambda *_a, **_k: {"park_weather_score": 0.5, "park_factor_available": True, "stadium_coordinates_available": True})
    out = agf.assemble_game_features({"game_id":"1","game_pk":1,"away_probable_pitcher":"a","home_probable_pitcher":"h","away_probable_pitcher_id":1,"home_probable_pitcher_id":2,"away_team_id":1,"home_team_id":2}, 2026, {}, {"source":"ok","available":True})
    assert out["feature_status"]["pitcher_stats_available"] and out["feature_status"]["team_offense_stats_available"]
    priced = predict_baseline(out)
    assert priced["probability_available"]


def test_pybaseball_failure_not_blocking(monkeypatch):
    monkeypatch.setattr(agf, "get_pitcher_stats", lambda *a, **k: {"available": True, "features": {"era": 3, "whip": 1.1}, "warnings": ["pybaseball call failed: HTTPError"]})
    monkeypatch.setattr(agf, "get_team_offense_stats", lambda *a, **k: {"available": True, "features": {"ops": 0.75, "runs_per_game": 4.8}, "warnings": []})
    monkeypatch.setattr(agf, "get_lineup_data", lambda *_a, **_k: {"lineups_confirmed": True, "warnings": []})
    monkeypatch.setattr(agf, "build_park_weather_features", lambda *_a, **_k: {"park_weather_score": 0.5, "park_factor_available": True, "stadium_coordinates_available": True})
    out = agf.assemble_game_features({"game_id":"1","game_pk":1,"away_probable_pitcher":"a","home_probable_pitcher":"h","away_probable_pitcher_id":1,"home_probable_pitcher_id":2,"away_team_id":1,"home_team_id":2}, 2026, {}, {"source":"ok","available":True})
    assert predict_baseline(out)["probability_available"]


def test_cli_summary_counts(monkeypatch, capsys):
    monkeypatch.setattr(build_today_board, "get_schedule", lambda _d: [{"game_id":"1","game_pk":1,"venue_id":1,"start_time":"2026-04-29T00:00:00Z","away_team":"A","home_team":"B"}])
    monkeypatch.setattr(build_today_board, "read_json", lambda *a, **k: [{"venue_id":1,"latitude":1,"longitude":1}])
    monkeypatch.setattr(build_today_board, "get_game_weather", lambda *a, **k: {"source":"ok","available":True})
    monkeypatch.setattr(build_today_board, "assemble_game_features", lambda *a, **k: {"feature_status":{"lineups_confirmed":False,"pitcher_stats_available":False,"team_offense_stats_available":False,"weather_available":False},"data_quality_score":0.4,"real_features":{},"warnings":[],"missing_data":[]})
    monkeypatch.setattr(build_today_board, "predict_baseline", lambda *a, **k: {"lean":"PASS","probability_available":False,"warnings":[],"feature_status":{"pitcher_stats_available":False,"team_offense_stats_available":False,"weather_available":False,"lineups_confirmed":False},"data_quality_score":0.4})
    build_today_board.run("2026-04-29")
    out = capsys.readouterr().out
    assert "Priced games:" in out and "Missing pitcher stats:" in out
