from first_inning_lab.data_sources import pybaseball_client as pb


def test_missing_optional_deps_safe(monkeypatch):
    monkeypatch.setattr(pb, "dependency_available", lambda _name: False)
    assert pb.get_pitching_stats_for_season(2026) == []
    assert pb.get_batting_stats_for_season(2026) == []
    assert pb.get_statcast_range("2026-04-01", "2026-04-10") == []
