from first_inning_lab.data_sources import mlb_stats_api as api


def test_normalize_game_shape():
    raw = {"gamePk": 123, "gameDate": "2026-04-29T23:05:00Z", "teams": {"away": {"team": {"name": "PHI", "id": 1}, "probablePitcher": {"fullName": "Away Pitcher", "id": 100}}, "home": {"team": {"name": "NYM", "id": 2}, "probablePitcher": {"fullName": "Home Pitcher", "id": 200}}}, "venue": {"name": "Citi Field", "id": 3}, "status": {"detailedState": "Scheduled"}}
    norm = api.normalize_game(raw)
    assert norm["game_pk"] == 123 and norm["away_team"] == "PHI"
    assert norm["game"] == "PHI @ NYM"
    assert norm["away_pitcher"] == "Away Pitcher"
    assert norm["home_pitcher"] == "Home Pitcher"
    assert norm["away_probable_pitcher"] == "Away Pitcher"
    assert norm["home_probable_pitcher"] == "Home Pitcher"


def test_first_inning_result_states(monkeypatch):
    monkeypatch.setattr(api, "get_linescore", lambda _pk: {"innings": [{"away": {"runs": 0}, "home": {"runs": 0}}]})
    assert api.get_first_inning_result(1)["result"] == "NRFI"
    monkeypatch.setattr(api, "get_linescore", lambda _pk: {"innings": [{"away": {"runs": 1}, "home": {"runs": 0}}]})
    assert api.get_first_inning_result(1)["result"] == "YRFI"
    monkeypatch.setattr(api, "get_linescore", lambda _pk: {"innings": [{"away": {"runs": None}, "home": {"runs": 0}}]})
    assert api.get_first_inning_result(1)["result"] == "PENDING"
    monkeypatch.setattr(api, "get_linescore", lambda _pk: {})
    assert api.get_first_inning_result(1)["result"] == "UNKNOWN"


def test_failed_api_response_no_crash(monkeypatch):
    monkeypatch.setattr(api, "safe_get_json", lambda *_a, **_k: {})
    assert api.get_schedule("2026-04-29") == []
